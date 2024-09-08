import os
import shutil
import os.path
import time
import shutil
import numpy as np
import netCDF4 as nc
import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable


"""
**********************************
DATA PROCESSING FUNCTIONS
**********************************
"""


"""
**********************************
WRITING APCEMM VARIABLES FUNCTIONS
**********************************
"""
def default_APCEMM_vars():
    location = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

    # Read the input file
    ip_file = open(os.path.join(location,'original.yaml'), 'r', newline='\n')
    op_lines = ip_file.readlines()
    ip_file.close()

    op_file = open(os.path.join(location,'input.yaml'), 'w', newline='\n')
    op_file.writelines(op_lines)
    op_file.close()

def write_shear(shear = 2e-3):
    location = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

    # Read the input file
    ip_file = open(os.path.join(location,'input.yaml'), 'r', newline='\n')
    op_lines = ip_file.readlines()
    ip_file.close()

    shear_idx = 57
    shear_line = op_lines[shear_idx]
    line_base = shear_line.split(':')[0]

    op_lines[shear_idx] = line_base + f": {shear}\n"

    op_file = open(os.path.join(location,'input.yaml'), 'w', newline='\n')
    op_file.writelines(op_lines)
    op_file.close()

"""
**********************************
READING APCEMM OUTPUTS FUNCTIONS
**********************************
"""
def initialise_output_directory():
    directory = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
    op_directory = os.path.join(directory, "outputs/")

    # See https://stackoverflow.com/a/273227
    if not os.path.exists(op_directory):
        os.makedirs(op_directory)

    # Delete the contents of the outputs directory. See https://stackoverflow.com/a/185941
    for file in sorted(os.listdir(op_directory)):
        file_path = os.path.join(op_directory,file)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

def save_APCEMM_raw_outputs(case_name):
    directory = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
    orig_dir = os.path.join(directory, "APCEMM_out/")
    dest_dir = os.path.join(directory, "outputs/raw/" + case_name + "/")

    # See https://stackoverflow.com/a/273227
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    # See https://stackoverflow.com/a/3399299
    for file_name in sorted(os.listdir(orig_dir)):
        full_file_name = os.path.join(orig_dir, file_name)
        if os.path.isfile(full_file_name):
            shutil.copy(full_file_name, dest_dir)

def process_and_save_outputs(filepath = "outputs/APCEMM-test-outputs.csv"):
    directory = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
    op_filepath = os.path.join(directory, filepath)
    directory = os.path.join(directory, "APCEMM_out/")

    # Initialise empty lists for the outputs of interest
    t_hrs = []
    width_m = []
    depth_m = []
    tau = []
    tau_int = []
    I = []
    N = []

    for file in sorted(os.listdir(directory)):
        if(file.startswith('ts_aerosol') and file.endswith('.nc')):
            file_path = os.path.join(directory,file)
            ds = xr.open_dataset(file_path, engine = "netcdf4", decode_times = False)

            # Calculate the time since formation from the filename
            tokens = file_path.split('.')
            mins = int(tokens[-2][-2:])
            hrs = int(tokens[-2][-4:-2])
            t_hrs.append(hrs + mins/60)

            # Save the variables that do not lie on a grid
            width_m.append(ds["width"].values[0])
            depth_m.append(ds["depth"].values[0])
            I.append(ds["Ice Mass"].values[0])
            N.append(ds["Number Ice Particles"].values[0])
            tau_int.append(ds["intOD"].values[0])

            # Calculate the average grid cell dimensions, and the number of grid cells
            x = ds["x"].values
            y = ds["y"].values
            dx = abs(x[-1] - x[0]) / len(x)
            dy = abs(y[-1] - y[0]) / len(y)

            # Extract the vertically integrated optical depth
            tau_vert = ds["Vertical optical depth"].values # It's a function of x

            # Populate the optical depth grid by undoing the integration
            tau_grid = np.zeros( (len(y), len(x) ) )
            for i in range(len(x)):
                tau_avg = tau_vert[i] / dy / len(y)
                tau_grid[:,i] = tau_avg

            # Integrate the optical depth over both x and y to calculate the average value
            tau_integ = 0
            tau_squared_integ = 0

            for i in range(len(x)):
                for j in range(len(y)):
                    tau_integ += tau_grid[j, i] * dx * dy
                    tau_squared_integ += tau_grid[j, i] ** 2 * dx * dy

            if tau_integ == 0:
                tau.append(0)
            else:
                tau.append(tau_squared_integ / tau_integ)

    t_hrs = np.array(t_hrs)
    width_m = np.array(width_m)
    depth_m = np.array(depth_m)
    tau = np.array(tau)
    tau_int = np.array(tau_int)
    I = np.array(I)
    N = np.array(N)

    data = {
        "Time Since Formation, h": t_hrs,
        "N, # / m": N,
        "Optical Depth, ---": tau,
        "Integrated Optical Depth, m": tau_int,
        "I, kg of ice / m": I,
        "Extinction defined width, m": width_m,
        "Extinction defined depth, m": depth_m,
    }

    op_filedir = os.path.dirname(op_filepath) # https://stackoverflow.com/a/10149358
    if not os.path.exists(op_filedir):
        os.makedirs(op_filedir)

    DF = pd.DataFrame.from_dict(data)
    DF.to_csv(op_filepath)

    return data

def reset_APCEMM_outputs():
    directory = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
    directory = os.path.join(directory, "APCEMM_out/")

    # See https://stackoverflow.com/a/273227
    if not os.path.exists(directory):
        os.makedirs(directory)

    # See See https://stackoverflow.com/a/185941
    for file in sorted(os.listdir(directory)):
        file_path = os.path.join(directory,file)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

def removeLow(arr, cutoff = 1e-3):
    func = lambda x: (x > cutoff) * x
    vfunc = np.vectorize(func)
    return vfunc(arr)



"""
**********************************
THERMODYNAMICS FUNCTIONS
**********************************
"""
def compute_p_sat_liq(T_K):
    # Calculates the liquid saturation pressure "p_sat_liq" (in units of Pa).
    # This equation can be found in Schumann 2012.
    # % 
    # % The inputs are as follows
    # %	- T_K is the absolute temperature in Kelvin
    a = -6096.9385
    b = 16.635794
    c = -0.02711193
    d = 1.673952e-5
    e = 2.433502

    return 100 * np.exp(a / T_K + b + c * T_K + d * T_K * T_K + e * np.log(T_K))

def compute_p_sat_ice(T_K):
    # Calculates the ice saturation pressure "p_sat_ice" (in units of Pa)
    # The equation can be found in Schumann 2012.
    #  
    # The inputs are as follows
    # - T_K is the absolute temperature in Kelvin

    a = -6024.5282
    b = 24.7219
    c = 0.010613868
    d = -1.3198825e-5
    e = -0.49382577

    return 100 * np.exp(a / T_K + b + c * T_K + d * T_K * T_K + e * np.log(T_K))

def convert_RH_to_RHi(T_K, RH):
    return RH * compute_p_sat_liq(T_K) / compute_p_sat_ice(T_K)

def convert_RHi_to_RH(T_K, RHi):
    return RHi * compute_p_sat_ice(T_K) / compute_p_sat_liq(T_K)

"""
**********************************
NIPC FUNCTIONS
**********************************
"""

def set_up_met(met_filepath = "inputs/met/test-APCEMM-met.nc"):
    directory = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
    source_filepath = os.path.join(directory, met_filepath)
    destination_filepath = os.path.join(directory, "current-APCEMM-met.nc")

    shutil.copyfile(source_filepath, destination_filepath)

def eval_APCEMM(met_filepath = "inputs/met/test-APCEMM-met.nc",
                output_filepath = "outputs/APCEMM-test-outputs.csv"):
    # # Default the variables
    # default_APCEMM_vars()

    # Eliminate the output files
    reset_APCEMM_outputs()

    # Copy the relevant met file to the example root folder
    set_up_met(met_filepath=met_filepath)

    # Run APCEMM
    os.system('./../../build_thresh2/APCEMM input.yaml')

    return process_and_save_outputs(filepath=output_filepath)

def run_from_met(mode = "sweep", initialise_opdir = True):
    """ Mode can be "sweep", "matrix", or "both" """

    if mode == "both":
        run_from_met(mode = "sweep", initialise_opdir = False)
        run_from_met(mode = "matrix", initialise_opdir = False)
        return 1

    if (mode != "sweep") & (mode != "matrix"):
        raise ValueError("Invalid input mode in run_from_met()")

    if initialise_opdir:
        initialise_output_directory()

    directory = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
    op_directory = os.path.join(directory, "outputs/" + mode + "/")
    met_directory_iter = os.path.join(directory, "inputs/met/" + mode + "/")
    met_directory_iter = os.fsencode(met_directory_iter)

    i = 1
    for file in os.listdir(met_directory_iter):
        met_filename = os.fsdecode(file)
        met_filepath = os.path.join("inputs/met/" + mode + "/", met_filename)

        case_name = met_filename[:-7]
        op_filepath = os.path.join(op_directory, case_name + "-OP.csv") 

        eval_APCEMM(
            met_filepath = met_filepath,
            output_filepath = op_filepath
        )

        save_APCEMM_raw_outputs(case_name)

        print(str(i) + " " + mode + " run(s) done")
        i += 1

    return 1

"""
**********************************
MAIN FUNCTION
**********************************
"""
if __name__ == "__main__" :
    casenum = 1
    start = time.time()
    
    run_from_met(mode = "sweep")
    
    end = time.time()
    runtime = end-start

    with open("runtimes.txt", 'a+') as f:
        f.write(f"Casenum {casenum} runtime: {runtime} seconds")
        
    # write_shear()