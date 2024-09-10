import os

def read_plume_model():
    f = open("Code.v05-00/src/Core/LAGRIDPlumeModel.cpp", "r")
    lines = f.readlines()
    f.close()
    return lines

def write_to_plume_model(lines):
    f = open("Code.v05-00/src/Core/LAGRIDPlumeModel.cpp", "w")
    f.writelines(lines)
    f.close()

def update_ithresh(ithresh: str = "1e6"):
    lines = read_plume_model()
    iline = lines[110]

    start_idx = iline.find('*') + 1
    end_idx = iline.find(')')
    iline_new = iline[:start_idx] + ithresh + iline[end_idx:]

    edited_lines = lines
    edited_lines[110] = iline_new
    write_to_plume_model(edited_lines)

def update_cthresh(cthresh: str = "0.01"):
    lines = read_plume_model()
    iline = lines[119]

    start_idx = iline.find('(') + 1
    end_idx = iline.find(')')
    iline_new = iline[:start_idx] + cthresh + iline[end_idx:]

    edited_lines = lines
    edited_lines[119] = iline_new
    write_to_plume_model(edited_lines)

def reset_plume_model():
    update_ithresh()
    update_cthresh()

def build_code(foldername):
    os.system(f"git submodule update --init --recursive")
    os.system(f"mkdir {foldername}")
    os.system(f"cd {foldername} && cmake ../Code.v05-00 && cmake --build .")

def edit_script(casename):
    scriptpath = f"examples/run_{casename}/run-APCEMM.py"
    f = open(scriptpath, "r")
    lines = f.readlines()
    f.close()

    lines_modified = lines
    lines_modified[273] = f"    os.system('./../../build_{casename}/APCEMM input.yaml')\n"

    f = open(scriptpath, "w")
    f.writelines(lines_modified)
    f.close()

def make_example(casename):
    # TODO: Debug this - it is doing sussy things
    os.system(f"cp -R examples/run_example examples/run_{casename}")
    edit_script(casename)        

def build_ithresh_code(ithresh_list):
    for ithresh in ithresh_list:
        casename = "icenum" + ithresh
        foldername = "build_" + casename
        reset_plume_model()
        update_ithresh(ithresh = ithresh)
        build_code(foldername)
        make_example(casename)

def build_cthresh_code(cthresh_list):
    for cthresh in cthresh_list:
        casename = "thresh" + cthresh
        foldername = "build_" + casename
        reset_plume_model()
        update_cthresh(cthresh = cthresh)
        build_code(foldername)
        make_example(casename)

def run_ithresh_code(ithresh_list):
    for ithresh in ithresh_list:
        casename = "icenum" + ithresh
        os.system(f"cd examples/run_{casename} && python3 run-APCEMM.py")

def run_cthresh_code(cthresh_list):
    for cthresh in cthresh_list:
        casename = "thresh" + cthresh
        os.system(f"cd examples/run_{casename} && python3 run-APCEMM.py")

if __name__ == "__main__":  
    cthresh_list = ["0.70", "0.80", "0.90"]
    build_cthresh_code(cthresh_list)
    # run_cthresh_code(cthresh_list)
