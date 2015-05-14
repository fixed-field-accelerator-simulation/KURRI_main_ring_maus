"""
Massage field map into the correct format
"""

import math

def cylindrical_to_cartesian(r, phi, axis):
    x = r*math.cos(phi)
    z = r*math.sin(phi)
    y = axis
    return (x, y, z)

def cylindrical_to_cartesian_alt(phi, br, bphi, baxis):
    bx = br*math.cos(phi)-bphi*math.sin(phi)
    bz = br*math.sin(phi)+bphi*math.cos(phi)
    by = baxis
    return (bx, by, bz)

def test_cylindrical_to_cartesian_alt():
    for i in range(0, 11):
        phi =  (-4.+i/100.*8.)*math.pi
        x0 = 1.
        y0 = 2.
        z0 = 3.
        x, z, y = cylindrical_to_cartesian_alt(phi, x0, y0, z0)
        if abs(x**2+y**2+z**2-x0**2-y0**2-z0**2) > 1e-9: # magnitude constant
            raise RuntimeError("Test fail 1")
        if abs(x-x0) < 1e-9 or abs(y-y0) < 1e-9 or abs(z-z0) > 1e-9: # transform applied
           if abs(math.cos(phi) - 1.) > 1e-9: # not 2 n pi
               print phi, "**", x0, y0, z0, "**", x, y, z
               raise RuntimeError("Test fail 2")
        x, z, y = cylindrical_to_cartesian_alt(-phi, x, y, z)
        if abs(x-x0) > 1e-9 or abs(y-y0) > 1e-9 or abs(z-z0) > 1e-9: # inverse applied
           raise RuntimeError("Test fail 3")
        x, z, y = cylindrical_to_cartesian_alt(math.pi/4., 1., 1., 0.)
        if abs(2.**0.5-y) > 1e-9 or abs(x) > 1e-9:
           raise RuntimeError("Test fail 4")
        x, z, y = cylindrical_to_cartesian_alt(3.*math.pi/4., 1., 1., 0.)
        if abs(2.**0.5+x) > 1e-9 or abs(y) > 1e-9:
           print x, y, z, 2.**0.5
           raise RuntimeError("Test fail 5")

def print_block(block):
    lines = []
    for i, line_in in enumerate(block):
        words = line_in.split()
        words[1] = i*math.pi/24./75.
        lines.append(words)
    for words in reversed(lines):
        r = float(words[0])
        phi = float(words[1])
        axis = float(words[2])
        br = float(words[3])
        baxis = float(words[4])
        bphi = float(words[5])
        x, y, z = cylindrical_to_cartesian(r, phi, axis)
        bx, by, bz = cylindrical_to_cartesian_alt(phi, br, bphi, baxis)
        print x, y, z, bx, baxis, bz
    # QUERY - SHOULD BZ BE NEGATIVE AFTER SYMMETRY POINT
    for words in lines[1:]:
        r = float(words[0])
        phi = float(words[1])
        axis = float(words[2])       
        br = float(words[3])
        baxis = float(words[4])
        bphi = float(words[5])
        phi = -phi
        x, y, z = cylindrical_to_cartesian(r, phi, axis)
        bx, by, bz = cylindrical_to_cartesian_alt(phi, br, bphi, baxis)
        print x, y, z, bx, by, bz

def main():
    """Main function"""
    field_map_in = open("fieldmaps/TOSCA_cyli13.H")
    for i in range(8):
        line = field_map_in.readline()
        print line,

    current_word = None
    block = []
    while True:
        line = field_map_in.readline()
        words = line.split()
        if current_word == None:
            current_word = words[2]
        if len(words) > 1 and words[2] == current_word: # still in same vertical step
            block.append(line)
        else: # new vertical step
            print_block(block)
            if line == '':
                break
            current_word = words[2] # vertical step
            block = [line]

if __name__ == "__main__":
    test_cylindrical_to_cartesian_alt()
    main()

