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

if __name__ == "__main__":
    ithresh_list = ["1e2", "1e4"]
    cthresh_list = ["0.1", "0.3", "0.5"]
    # dir_path = os.path.dirname(os.path.realpath(__file__))
    # print(dir_path)

    for ithresh in ithresh_list:
        foldername = "build_icenum" + ithresh
        reset_plume_model()
        update_ithresh(ithresh = ithresh)
        build_code(foldername)

    for cthresh in cthresh_list:
        foldername = "build_thresh" + cthresh
        reset_plume_model()
        update_cthresh(cthresh = cthresh)
        build_code(foldername)
