import copy
import math
import xboa.common
import maus_cpp.globals
import maus_cpp.field
import json
import Configuration

def convert_to_polar(item, scale):
    r = (item[0]**2+item[1]**2)**0.5
    phi = math.atan2(item[1], item[0])
    item[0] = r
    item[1] = phi
    br   = +math.cos(phi)*item[3] + math.sin(phi)*item[4]
    bphi = -math.sin(phi)*item[3] + math.cos(phi)*item[4]
    item[3] = br
    item[4] = bphi
    for j in range(6):
        if scale != None:
            item[j] *= scale[j]
    return item

def b_field_search():
    for x in range(-10000, 10000, 100):
        for y in range(-10000, 10000, 100):
            bx, by, bz, ex, ey, ez = maus_cpp.field.get_field_value(x, 0., y, 0.)
            if (bx**2+by**2+bz**2)**0.5 > 1.e-9:
                print x, y, 0., "**", bx, by, bz
        print x

def read_fields_maus(r_min, r_max, r_step, y_min, y_max, y_step, phi_min, phi_max, phi_step):
    r, y, phi = r_min, y_min, phi_min
    fields = []
    while r < r_max:
        while y < y_max:
            while phi < phi_max:
                x, z = r*math.cos(phi), r*math.sin(phi)
                bx, by, bz, ex, ey, ez = maus_cpp.field.get_field_value(x, y, z, 0.)
                words = [x, z, y, bx, bz, by]
                words = convert_to_polar(words, [1., 1., 1., 1e3, 1e3, 1e3])
                fields.append(words)
                phi += phi_step
                print fields[-1]
            y += y_step
        r += r_step
    print "Found", len(fields), "elements"
    print fields[0], fields[-1]
    return fields

def read_fields_opal(file_name, start_key, stop_key, skip_key, scale = None):
    print "Loading", file_name, "with keys", start_key, stop_key

    fin = open(file_name)
    started = False
    polar_field_list = []

    for line in fin.readlines():
        if line.find(stop_key) > -1:
            break
        if started:
            if line.find(skip_key) > -1:
                continue
            try:
                item = [float(word) for word in line.split()]
                if len(item) != 6:
                    continue
                #print "Raw", line.rstrip("\n")
                polar_field_list.append(convert_to_polar(item, scale))
                #print "Polar", polar_field_list[-1]
            except ValueError:
                if line.find("B Cycl:") > -1 or line.find("B global:") > -1:
                    print line.rstrip("\n")
        if line.find(start_key) > -1:
            started = True
    print "Found", len(polar_field_list), "elements"
    print polar_field_list[0], polar_field_list[-1]
    return polar_field_list

def plot_fields_1d(field_map, b_index, canvas = None, phi_offset = 0., legend_list = None, name = ""):
    b_name = {3:"r", 4:"#phi", 5:"z"}[b_index]
    phi_list, b_list = [], []
    r = field_map[0][0]
    y = field_map[0][2]
    if legend_list == None:
        legend_list = []
    for item in field_map:
        if abs(item[2] - y) > 1e-3 or abs(item[0] - r) > 1e-3 or item == field_map[-1]:
            ymax = max([abs(b) for b in b_list])*1.1
            print "Plotting for y:", y, "r:", r
            hist, graph = xboa.common.make_root_graph("B"+b_name, phi_list, "phi [rad]", b_list, "B_{"+b_name+"} [T]", ymax=ymax, ymin=-ymax)
            graph.SetName(name+" B_{"+b_name+"} r = "+str(r)+" y = "+str(y))
            if canvas == None:
                canvas = xboa.common.make_root_canvas("b_"+b_name+"_"+name)
                hist.Draw()
            graph.SetMarkerColor(len(legend_list)+1)
            graph.SetMarkerStyle(6)
            graph.SetLineColor(10)
            graph.Draw('p')
            legend_list.append(graph)
            phi_list, by_list = [], []
            y = item[2]
            r = item[0]
        phi_list.append(item[1]+phi_offset)
        b_list.append(item[b_index])
    return canvas, legend_list

def plot_b_opal():
    file_name = "/home/cr67/OPAL/work/kurri_main_ring/tmp/tune/2/log"
    field_map_n = read_fields_opal(file_name, "Write3DFieldMap 3", "Write3DFieldMap 5", "**", [1.]*3+[-0.1]*3)
    field_map_0 = read_fields_opal(file_name, "Write3DFieldMap 1", "Write3DFieldMap 2", "**", [1.]*3+[-0.1]*3)
    field_map_p = read_fields_opal(file_name, "Write3DFieldMap 2", "Write3DFieldMap 3", "**", [1.]*3+[-0.1]*3)
    for i in range(3, 6):
        canvas, legend_list = None, None
        for field_map in [field_map_p, field_map_0, field_map_n]:
            if len(field_map) == 0:
                print "No data"
                continue
            canvas, legend_list = plot_fields_1d(field_map, i, canvas, 0., legend_list, "OPAL")
        xboa.common.make_root_legend(canvas, legend_list)
        canvas.Update()
        #canvas_name = canvas.GetName()[:-2]
        #for format in ["png", "root", "eps"]:
            #print canvas_name+"."+format
            #canvas.Print("plots/"+canvas_name+"."+format)

def plot_b_maus():
    for i in range(3, 6):
        canvas, legend_list = None, None
        for y in [1., 0., -1.]:
            field_map_maus = read_fields_maus(4600., 4601, 99., y, y+0.1, 99., -math.pi/12., 5.*math.pi/12., math.pi/6./300.)
            canvas, legend_list = plot_fields_1d(field_map_maus, i, canvas, 0., legend_list, "maus")
        xboa.common.make_root_legend(canvas, legend_list)
        canvas.Update()
        #canvas_name = canvas.GetName()[:-2]
        #for format in ["png", "root", "eps"]:
            #print canvas_name+"."+format
            #canvas.Print("plots/"+canvas_name+"."+format)



def main():
    file_name = "lattices/ads_geometry_fieldmaps_f810_d1020.dat"
    my_datacards = {
        "simulation_geometry_filename":file_name,
    }
    datacards = json.loads(Configuration.Configuration().getConfigJSON())
    for item in my_datacards.keys():
        datacards[item] = my_datacards[item]
    maus_cpp.globals.birth(json.dumps(datacards))
    #b_field_search()
    plot_b_maus()
    plot_b_opal()

if __name__ == "__main__":
    main()
    raw_input()
