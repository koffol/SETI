import random
import cProfile
from math import *
import numpy as np
import tools
# ===================== #
#        CONSTANTS      #
# ===================== #
pc = 1.
sec = 1.
M_solar = 1.

meter = 1./3.086e16 #km
km = 1./3.086e13  # pc
year = 3.154e7*sec  # s
Myr = 1.e6*year  # s
kg = 1./1.1988435e30  # M_solar
cSpeed = 3.e5*km/sec  # pc/s
Gconst = 6.67e-11 #N.m^2.kg^-2 = kg^1.m^1.s^-2.m^2.kg^-2 = kg^-1.m^3.s^-2 
Gconst = Gconst*meter**3/(kg*sec**2)
# ===================== #
#        HANDLES        #
# ===================== #
N_disk = int(5.e3)  # number of particles in disk (same order as N_gal)
#dt = np.logspace(-1, 1, num=1)*Myr  # galactic rotation time step
dt = 0.01*Myr
#dt_const = np.logspace(-12, 1, num=1)*Myr  # construction time delay
dt_const = 1e-13*Myr
#VC = np.logspace(2, 0, num=1)*cSpeed  # probe velocity
VC = 1e-2*cSpeed
t = 0
t_f = 1.e3*Myr  # time to stop
SingleProbe = True
InfiniteProbe = not(SingleProbe)
coveringFraction = 1.0
RandomStart = False
# Change below only if RandomStart = False
start_r = 8e3  # radial distance from the galactic center in pc
r_err = 100.
name = 'bulge_cf1_single'
# ===================== #
#  Galactic parameters  #
# ===================== #
# DISK
N_thin = int(0.90*N_disk)
N_thick = int(N_disk-N_thin)
h_z_thin = 3.e2  # scale height of the thin disk (pc)
h_z_thick = 5.e2  # scale height of the thick disk (pc)
h_rho_disk = 5.e3  # scale length of the thin disk (pc)
I_0_disk = 20.e9  # disk central intensity
alpha_disk = h_rho_disk  # disk scale length (pc)
n_s_disk = 1  # disk Sersic index
M_disk = 6.e10  # disk mass
#FIXME values
mean_rho_disk = 50.*km/sec
sigma_rho_disk = 40.*km/sec
mean_z_disk = 10.*km/sec
sigma_z_disk = 3.*km/sec

# BULGE
#N_bulge = int(0.33000*N_disk)
## Maybe this is too small after all...
N_bulge = int(0.01*N_disk)
#N_bulge = 0
R_bulge = 2.7e3  # bulge radius
I_0_bulge = 5.e9  # bulge central intensity
alpha_bulge = R_bulge/3.  # bulge scale length
n_s_bulge = 5  # Bulge Sersic index(in range: 1.5-10)
M_bulge = 9.3e6  # bulge mass #FIXME
#M_bulge = 2.e10  # bulge mass
mean_bulge = 200.*km/sec # (My arbitrary value!!) #FIXME value
sigma_bulge = 130.*km/sec # Velocity dispercion

# Halo (NOT included!)
N_halo = 0
R_halo = 1.e8
I_0_halo = 5.e6  # bulge central intensity
alpha_halo = R_halo/3.  # bulge scale length
n_s_halo = 5  # Bulge Sersic index(in range: 1.5-10)
mean_halo = 200.*km/sec # (My arbitrary value!!)
sigma_halo = 130.*km/sec # Velocity dispercion
M_halo = 2.e10  # bulge mass

#GALAXY
alpha_gal = alpha_disk
N_gal = N_disk + N_bulge + N_halo
M_DM = 2.e12  # dark halo mass(M_solar)
M_gal = M_disk + M_bulge + M_DM
L2Lstar = np.power((M_gal/2.e12*M_solar), 2)
R_opt = 2.*h_rho_disk # Optical radius
V_opt = 300.*km/sec # V(R_opt)
n_s_gal = 4
# ========================== #
#    Initialisation (t=0)    #
# ========================== #
# POS:Thin disk (Cylindrical)
rho_thin= tools.init_pos(N_thin, 0., h_rho_disk, 'exp')
phi_thin = tools.init_pos(N_thin, 0., 2*pi, 'uni')
z_thin = tools.init_z(N_thin, 0., h_z_thin, 'exp')

# POS:Thick disk (Cylindrical)
rho_thick = tools.init_pos(N_thick, 0, h_rho_disk, 'exp')
phi_thick = tools.init_pos(N_thick, 0., 2*pi, 'uni')
z_thick = tools.init_z(N_thick, 0., h_z_thick, 'exp')

# POS:Disk (Cylindrical)
rho_disk = np.append(rho_thin, rho_thick)
phi_disk = np.append(phi_thin, phi_thick)
z_disk = np.append(z_thin, z_thick)

# POS:Bulge (Spherical)
r_bulge = tools.init_pos(N_bulge, 0., R_bulge, 'uni')  #galaxy[0]
phi_bulge_sph = tools.init_pos(N_bulge, 0., pi, 'uni')  #galaxy[1]
theta_bulge = tools.init_pos(N_bulge, 0., 2.*pi, 'uni')  #galaxy[2]

# POS:Bulge (Cylindrical)
rho_bulge = r_bulge*np.sin(phi_bulge_sph)
z_bulge = r_bulge*np.cos(phi_bulge_sph)
phi_bulge = theta_bulge

# POS:Halo (Spherical)
r_halo = tools.init_pos(N_halo, 0., R_halo, 'uni') #galaxy[0]
phi_halo = tools.init_pos(N_halo, 0., pi, 'uni') #galaxy[1]
theta_halo = tools.init_pos(N_halo, 0., 2.*pi, 'uni') #galaxy[2]

# POS:Halo (Cylindrical)
rho_halo = r_halo*np.sin(phi_halo)
z_halo = r_halo*np.cos(phi_halo)
phi_halo = theta_halo

# VEL:Disk (Rotation curve analytic relation)
Vrho_disk = np.zeros(N_disk)
Vphi_disk = tools.v_rotational(rho_disk, V_opt, R_opt, L2Lstar)
Vz_disk = np.zeros(N_disk)

# VEL:Bulge (Gaussian dist. with given mean and dispersion)
#Vrho_bulge = np.random.normal(mean_bulge, 2.*sigma_bulge, N_bulge) #galaxy[6]
Vrho_bulge = np.zeros(N_bulge)

Vphi_bulge = np.random.normal(mean_bulge, 2.*sigma_bulge, N_bulge) #galaxy[3]
#inc_bulge = tools.init_pos(N_bulge, -0.5*pi, 0.5*pi, 'uni')
#FIXME
omega_bulge = np.sqrt(Gconst*M_bulge/(R_bulge)**3)  # [1/s]
#Vphi_bulge = r_bulge*km*omega_bulge  # [km/s] 
Vz_bulge = np.zeros(N_bulge)
#Vz_bulge = np.random.normal(mean_bulge, 2.*sigma_bulge, N_bulge) #galaxy[7]

# VEL:Halo (Gaussian dist. with given mean and dispersion)
Vrho_halo = tools.init_norm(mean_halo, sigma_halo, N_halo)
Vphi_halo = tools.init_norm(mean_halo, sigma_halo, N_halo)
Vz_halo = tools.init_norm(mean_halo, sigma_halo, N_halo)

# I(I-band):Disk
I_disk = tools.init_sersic(I_0_disk, alpha_disk, n_s_disk, rho_disk)

# L(I-band):Bulge (Gaussian dist. with given total L)
lgI_I0 = np.power(rho_bulge, 0.25)
I_bulge = I_0_bulge*np.exp(-lgI_I0)

# L(I-band):Halo (Gaussian dist. with given total L)
lgI_I0 = np.power(rho_halo, 0.25)
I_halo = I_0_halo*np.exp(-lgI_I0)

# POS:Galaxy
rho_gal = np.append(rho_bulge, rho_disk)
rho_gal = np.append(rho_gal, rho_halo)
phi_gal = np.append(phi_bulge, rho_disk)
phi_gal = np.append(phi_gal, phi_halo)
z_gal = np.append(z_bulge, z_disk)
z_gal = np.append(z_gal, z_halo)
Vrho_gal = np.append(Vrho_bulge, Vrho_disk)
Vrho_gal = np.append(Vrho_gal, Vrho_halo)
Vphi_gal = np.append(Vphi_bulge, Vphi_disk)
Vphi_gal = np.append(Vphi_gal, Vphi_halo)
Vz_gal = np.append(Vz_bulge, Vz_disk)
Vz_gal = np.append(Vz_gal, Vz_halo)

# This is just to keep the galaxy array consistent, NOT for SB measurement
I_gal = np.append(I_bulge, I_disk)
I_gal = np.append(I_gal, I_halo)
Li = np.sum(I_gal)

# Galaxy 6-D array
galaxy = np.zeros((8, N_gal))
galaxy[0] = rho_gal
galaxy[1] = phi_gal
galaxy[2] = z_gal
galaxy[3] = Vphi_gal
galaxy[4] = I_gal
# CS:Galaxy (Colonisation Status)
if RandomStart:
    CS_gal = tools.CS_random(N_gal)
else:
    CS_gal, r_colonizer = tools.CS_manual(N_gal, galaxy, start_r, r_err)
galaxy[5] = CS_gal
galaxy[6] = Vrho_gal
galaxy[7] = Vz_gal

#galaxy_inds = {"rho": 0, "phi": 1, "z", 2, "Vphi": 3, "I": 4, "CS": 5, "Vrho": 6, "Vz": 7}

## Initial plotting
#x_gal=rho_gal*np.cos(phi_gal)
#y_gal=rho_gal*np.sin(phi_gal)

def update():
    global t
# ============== #
#    UPDATING    #
# ============== #
    count = 1
    i = 0
    col_tot = 0.
    count_tot = 0.
#    print "CS"
    colonized_fraction = np.sum(galaxy[5])/len(galaxy[5])
    print "%.2f colonized"%(colonized_fraction)
    print "Writing to file..."
    filename = "galaxy_%.0f"%(t/Myr)
    np.save(filename, galaxy)
#    tools.plot_cont_galaxy(t, x_gal, y_gal, z_gal, I_gal, start_r, I_gal)

#    while colonized_fraction < 0.9:
    while t < t_f:
        galaxy_cart = np.zeros((3,(N_bulge+N_disk+N_halo)))
        galaxy_cart[0]=galaxy[0]*np.cos(galaxy[1])
        galaxy_cart[1]=galaxy[0]*np.sin(galaxy[1])
        galaxy_cart[2]=galaxy[2]

        t = i*dt

        # Colonize the galaxy!
        dist = VC * (dt-dt_const)
        ## how about the case where dt_const is larger?
        if SingleProbe:
            galaxy[4], galaxy[5], colonized, count, ind_dmin = tools.col_single(galaxy, galaxy_cart, dist, count, coveringFraction)
        elif InfiniteProbe:
            ind = np.where(CS_gal==1)[0]
            galaxy[4], galaxy[5], colonized, count = tools.col_inf(galaxy, galaxy_cart, dist, count, ind, coveringFraction)

#        if i==2 or i==10 or i==20 or i==1000:

        colonized_fraction = np.sum(galaxy[5])/len(galaxy[5])
        if np.round(colonized_fraction)==0.2 or np.round(colonized_fraction)==0.5:

            # galaxy_cart = np.zeros((3,(N_bulge+N_disk+N_halo)))
            # galaxy_cart[0]=galaxy[0]*np.cos(galaxy[1])
            # galaxy_cart[1]=galaxy[0]*np.sin(galaxy[1])
            # galaxy_cart[2]=galaxy[2]
            print "%.2f colonized"%(colonized_fraction)
            print "Writing to file..."
            filename = "galaxy_%.0f"%(t/Myr)
            np.save(filename, galaxy)
#            tools.plot_cont_galaxy(t, galaxy_cart[0], galaxy_cart[1], galaxy_cart[2], galaxy[4], start_r, I_gal, colonized_fraction)
    
    # Rotate the galaxy!
#        Vrho_template = np.random.normal(mean_rho_disk, 2.*sigma_rho_disk, int(N_disk/9))
#        Vz_template =  np.random.normal(mean_z_disk, 2.*sigma_z_disk, int(N_disk/9))
    
    # DISK
    #ALT1
        # Vrho_p = np.random.normal(mean_rho_disk, 2.*sigma_rho_disk, N_disk/2.)
        # Vrho_n = np.random.normal(-mean_rho_disk, 2.*sigma_rho_disk, N_disk/2.)
        # galaxy[6,N_bulge:] =np.append(Vrho_p, Vrho_n)

        # Vphi_disk = tools.v_rotational(rho_disk, V_opt, R_opt, L2Lstar)
        # Vz_p = np.random.normal(mean_z_disk, 2.*sigma_z_disk, N_disk/2.)
        # Vz_n = np.random.normal(-mean_z_disk, 2.*sigma_z_disk, N_disk/2.)
        # galaxy[7,N_bulge:] = np.append(Vz_p, Vz_n)
    #ALT2
        sign = np.round(np.random.uniform(0,1,N_disk))*2.-1
        galaxy[6,N_bulge:] = sign*np.random.normal(mean_rho_disk, 2.*sigma_rho_disk, N_disk)
        sign = np.round(np.random.uniform(0,1,N_disk))*2.-1
        galaxy[7,N_bulge:] = sign*np.random.normal(mean_z_disk, 2.*sigma_z_disk, N_disk)

    # BULGE
        #ALT1
        # Vphi_p = np.random.normal(mean_bulge, 2.*sigma_bulge, N_bulge/2)
        # Vphi_n = np.random.normal(-mean_bulge, 2.*sigma_bulge, N_bulge/2)
        # galaxy[3,:N_bulge] = np.append(Vphi_p, Vphi_n)

        # Vrho_p = np.random.normal(mean_bulge, 2.*sigma_bulge, N_bulge/2)
        # Vrho_n = np.random.normal(-mean_bulge, 2.*sigma_bulge, N_bulge/2)
        # galaxy[6,:N_bulge] = np.append(Vrho_p, Vrho_n)

        # Vz_p = np.random.normal(mean_bulge, 2.*sigma_bulge, N_bulge/2)
        # Vz_n = np.random.normal(-mean_bulge, 2.*sigma_bulge, N_bulge/2)
        # galaxy[7,:N_bulge] = np.append(Vz_p, Vz_n)

        #ALT2
        # sign = np.round(np.random.uniform(-1,1,N_bulge))
        # galaxy[3,:N_bulge] = sign*np.random.normal(mean_bulge, 2.*sigma_bulge, N_bulge)
        # galaxy[6,:N_bulge] = sign*np.random.normal(mean_bulge, 2.*sigma_bulge, N_bulge)
        # galaxy[7,:N_bulge] = sign*np.random.normal(mean_bulge, 2.*sigma_bulge, N_bulge)

        sign = np.round(np.random.uniform(0,1,N_bulge))*2.-1
        galaxy[3,:N_bulge] = sign*np.random.normal(mean_bulge, 2.*sigma_bulge, N_bulge)
        sign = np.round(np.random.uniform(0,1,N_bulge))*2.-1
        galaxy[6,:N_bulge] = sign*np.random.normal(mean_bulge, 2.*sigma_bulge, N_bulge)/galaxy[0,:N_bulge]
        sign = np.round(np.random.uniform(0,1,N_bulge))*2.-1
        galaxy[7,:N_bulge] = sign*np.random.normal(mean_bulge, 2.*sigma_bulge, N_bulge)

        galaxy[0] += galaxy[6]*dt
        galaxy[1] += (galaxy[3]/galaxy[0])*dt
        galaxy[2] += galaxy[7]*dt

        i += 1
#galaxy_inds = {"rho": 0, "phi": 1, "z", 2, "Vphi": 3, "I": 4, "CS": 5, "Vrho": 6, "Vz": 7}

    # galaxy_cart = np.zeros((3,(N_bulge+N_disk+N_halo)))
    # galaxy_cart[0]=galaxy[0]*np.cos(galaxy[1])
    # galaxy_cart[1]=galaxy[0]*np.sin(galaxy[1])
    # # DISK
    # galaxy_cart[2,N_bulge:]=galaxy[2,N_bulge:]
    # # BULGE
    # galaxy_cart[2,0:N_bulge]=galaxy[0,0:N_bulge]*np.cos(galaxy[1,0:N_bulge])

    print "%.2f colonized"%(colonized_fraction)
    print "Writing to file..."
    filename = "galaxy_%.0f"%(t/Myr)
    np.save(filename, galaxy)
#    tools.plot_cont_galaxy(t, galaxy_cart[0], galaxy_cart[1], galaxy_cart[2], galaxy[5], start_r, I_gal, colonized_fraction)
cProfile.run("update()", "stats")

# ==================== #
#        PLOTTING      #
# ==================== #
#if SingleProbe:
#    tools.singleplot(name, N_gal, Li, r_colonizer, VC, dt_const)
#elif InfiniteProbe:
#    tools.infplot(name, N_gal, Li, r_colonizer, VC, dt_const)
#tools.plot_cont_galaxy(galaxy_cart)
