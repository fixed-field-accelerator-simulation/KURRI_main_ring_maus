import glob
import json
import sys
import os
import shutil
import math
import ROOT
import Configuration
import xboa
from xboa.tracking import MAUSTracking
import xboa.common as common
from xboa.hit import Hit
from xboa.algorithms.tune import DPhiTuneFinder

class Tune(object):
    def __init__(self, file_name):
        """
        Find the tune. If file_name is specified, use that file_name, otherwise
        generate a new one by tracking
        """
        self.closed_orbits_cached = None
        self.tmp_dir = None
        self.just_plot = file_name != None
        self.lattice_src = "lattices/ads_geometry_fieldmaps_f810_d1020.dat"
        self._load_closed_orbits("closed_orbits_low_energy.ref")
        self.nturns = 10.1
        self.step_size = 10.
        self.poly_order = 1
        self.smooth_order = 1
        self.delta_x = 1.
        self.delta_y = 1
        self.string_id = "_nturns="+str(self.nturns)+"_stepsize="+str(self.step_size)
        self.output = "tunes"+self.string_id+".out"
        self.co_x = None

    def get_tracking(self):
        max_steps = int(6000.*self.nturns*2.*math.pi/self.step_size)
        my_datacards = {
            "simulation_geometry_filename":self.lattice_src,
            "max_step_length":self.step_size,
            "verbose_level":5,
            "maximum_number_of_steps":max_steps,
            "physics_processes":"none",
        }
        datacards = json.loads(Configuration.Configuration().getConfigJSON())
        for item in my_datacards.keys():
            datacards[item] = my_datacards[item]
        tracking = xboa.tracking.MAUSTracking(datacards, 0)
        return tracking

    def find_tune_dphi(self):
        fout = open(self.output, "w")
        index = 0
        for energy, position in sorted(self.closed_orbits_cached.iteritems()):
            index += 1
            if index > 2:
                ROOT.gROOT.SetBatch(True)
            print "Finding tune at", energy, "MeV and closed orbit x=", position, "mm"
            hit = self._reference(energy)
            hit["x"] = position
            self.co_x = position
            tune_info = {
                "energy":energy,
                "nturns":self.nturns,
                "stepsize":self.step_size,
                "poly_order":self.poly_order,
                "smooth_order":self.smooth_order,
            }
            for axis1, delta1, axis2, delta2 in [("x", self.delta_x, "px", 0.), ("y", self.delta_y, "py", 0.)]:
                tracking = self.get_tracking()
                finder = DPhiTuneFinder()
                finder.run_tracking(axis1, axis2, delta1, delta2, hit, tracking)
                tune = finder.get_tune(self.nturns/10.)
                tune_info[axis1+"_tune"] = tune
                tune_info[axis1+"_tune_error"] = finder.tune_error
                tune_info[axis1+"_signal"] = zip(finder.u, finder.up)
            for key in sorted(tune_info.keys()):
                if "signal" not in key:
                    print "   ", key, tune_info[key]
            print >> fout, json.dumps(tune_info)
            fout.flush()

    def _temp_dir(self):
        self.tmp_dir = "tmp/tune/"+str(self.unique_id)+"/"
        if self.just_plot:
            return
        try:
            shutil.rmtree(self.tmp_dir)
        except OSError:
            pass
        os.makedirs(self.tmp_dir)

    def _load_closed_orbits(self, filename):
        fin = open(filename)
        closed_orbits = [json.loads(line) for line in fin.readlines()]
        closed_orbits_energy = [orbit[0] for orbit in closed_orbits]
        closed_orbits_x = [orbit[1:][0][0] for orbit in closed_orbits]
        closed_orbits_dict = dict(zip(closed_orbits_energy, closed_orbits_x))
        self.closed_orbits_cached = closed_orbits_dict

    def _reference(self, energy):
        hit_dict = {}
        hit_dict["pid"] = 2212
        hit_dict["mass"] = common.pdg_pid_to_mass[2212]
        hit_dict["charge"] = 1
        hit_dict["x"] = 4600.
        hit_dict["kinetic_energy"] = energy
        return Hit.new_from_dict(hit_dict, "pz")

    def _print_canvas(self, canvas, axis, name, energy):
        name = "plots/"+axis+"_"+name+"_energy="+str(energy)+self.string_id
        for format in ["png", "root"]:
            canvas.Print(name+"."+format)

def main():
    tune = Tune(None)
    tune.find_tune_dphi()

if __name__ == "__main__":
    main()
    print "Finished"
    raw_input()

