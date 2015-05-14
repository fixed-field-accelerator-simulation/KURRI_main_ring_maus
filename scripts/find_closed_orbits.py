import StringIO
import math
import sys
import json
sys.path.insert(1, "scripts")
import Configuration
import xboa
from xboa.tracking import MAUSTracking
import xboa.common as common
from xboa.hit import Hit
from xboa.algorithms.closed_orbit import EllipseClosedOrbitFinder
from xboa.bunch import Bunch

import ROOT

def reference(energy):
    hit_dict = {}
    hit_dict["pid"] = 2212
    print common.pdg_pid_to_name[2212]
    hit_dict["mass"] = common.pdg_pid_to_mass[2212]
    hit_dict["charge"] = 1
    hit_dict["x"] = 4600.
    hit_dict["kinetic_energy"] = energy
    return Hit.new_from_dict(hit_dict, "pz")

def plot_iteration(i, iteration, energy, step):
    canvas, hist, graph, fit = iteration.plot_ellipse("x", "px", "mm", "MeV/c")
    hist.SetTitle('KE='+str(energy)+' iter='+str(i))
    canvas.Update()
    name = "plots/closed_orbit-i_"+str(i)+"-ke_"+str(energy)+"-step_"+str(step)
    canvas.Print(name+".root")
    canvas.Print(name+".png")

def get_tracking(energy, nturns, step, seed):
    my_datacards = {
        "simulation_geometry_filename":"lattices/ads_geometry_fieldmaps_f810_d1020.dat",
        "max_step_length":step,
        "verbose_level":1,
        "maximum_number_of_steps":int(nturns*(4835.+seed[0])*2.*math.pi/step),
    }
    datacards = json.loads(Configuration.Configuration().getConfigJSON())
    for item in my_datacards.keys():
        datacards[item] = my_datacards[item]
    tracking = xboa.tracking.MAUSTracking(datacards, 0)
    return tracking

def plot_steps(seed_track):
    track = []
    for a_track in seed_track:
        track += a_track
    print len(seed_track)
    bunch = Bunch.new_from_hits(track)
    for hit in bunch:
        print hit['x'], hit['y'], hit['z'], hit['t']
    canvas, hist, graph = bunch.root_scatter_graph("x", "z", "mm", "mm")
    graph.SetMarkerStyle(4)
    graph.Draw('p')
    canvas, hist, graph = bunch.root_scatter_graph("x", "y", "mm", "mm")
    graph.SetMarkerStyle(4)
    graph.Draw('p')
    canvas, hist, graph = bunch.root_scatter_graph("x", "px", "mm", "MeV/c")
    graph.SetMarkerStyle(4)
    graph.Draw('p')
    return

def find_closed_orbit(energy, nturns, step, seed):
    print "Energy", energy, "NTurns", nturns, "StepSize", step, "Seed", seed
    tracking = get_tracking(energy, nturns, step, seed)
    ref_hit = reference(energy)
    mass = common.pdg_pid_to_mass[2212]
    seed_hit = ref_hit.deepcopy()
    seed_hit["x"] = seed[0]
    print "Primary"
    print seed_hit['x'], seed_hit['y'], seed_hit['z'], seed_hit['t']
    tracking.track_one(seed_hit)
    print "Tracking"
    plot_steps(tracking.last)
    finder = EllipseClosedOrbitFinder(tracking, seed_hit)
    generator = finder.find_closed_orbit_generator(["x", "px"], 1)
    for i, iteration in enumerate(generator):
        for hit in tracking.last[0]:
            print hit['station'], hit['t'], hit['x'], hit['px']
        plot_iteration(i, iteration, energy, step)
        print iteration.points
        if i >= 5:
            print "Ran up to 5 iterations"
            break
        if iteration.centre != None and abs(iteration.points[-1][0] - iteration.centre[0]) < 0.01 and abs(iteration.points[-1][1]) < 0.01: # 10 micron tolerance
            print "Reached closed orbit tolerance"
            break

    plot_iteration(i, iteration, energy, step)
    return tracking.last[-1]

if __name__ == "__main__":
      next_seed = [4413., 0., 0.] # [5153., 0.0] # 
      fout = open('find_closed_orbit.out', 'w')
      energy_list = range(11, 13, 1)
      for i, energy in enumerate(energy_list):
          is_batch = i > 5
          ROOT.gROOT.SetBatch(is_batch)
          hit_list = find_closed_orbit(energy, 10., 10, next_seed)
          print hit_list
          next_seed = [hit_list[0]["x"], 0.]
          output = [energy]+[[hit["x"], hit["t"]] for hit in hit_list]
          print >> fout, json.dumps(output)
          fout.flush()
      print "finished"
      if is_batch:
          raw_input()

