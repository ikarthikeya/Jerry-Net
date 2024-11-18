import numpy as np


def ll_to_xyz(lat, lon):
    x = np.cos(np.radians(lat)) * np.cos(np.radians(lon))
    y = np.cos(np.radians(lat)) * np.sin(np.radians(lon))
    z = np.sin(np.radians(lat))
    return x,y,z


def xyz_to_ll(x,y,z):
    lat = np.arcsin(z)
    lon = np.arctan2(y, x)
    return np.degrees(lat), np.degrees(lon)


def rotation_matrix_with_angle(alpha, beta):
    assert (-90 <= alpha <= 90 and -180 <= beta <= 180), "latitude rotation must be from -90 to 90, longitude rotation must be from -180 to 180"
    alpha = np.radians(alpha)
    beta = np.radians(beta)
    R_beta = np.array([[np.cos(beta),-np.sin(beta),0],
                       [np.sin(beta), np.cos(beta),0],
                       [0,0,1]])
    R_alpha = np.array([[1,0,0],
                        [0,np.cos(alpha),-np.sin(alpha)],
                        [0,np.sin(alpha),np.cos(alpha)]])
    R = R_alpha.dot(R_beta)
    return R


def init_satellites(orbit_z_axis,num_sat):
    alpha, beta = orbit_z_axis
    rotation = rotation_matrix_with_angle(alpha, beta)
    # we assume satellites are moving on an equator orbit
    # init satellites with equal distance between each other on the equator orbit
    lats = np.zeros((num_sat,))
    lons = np.arange(-180,180,360.0/num_sat)
    xs,ys,zs = ll_to_xyz(lats,lons)
    xyz_orbit = np.vstack((xs,ys,zs)) # the shape should be [3,num_sat]
    xyz_world = np.linalg.inv(rotation).dot(xyz_orbit)
    x_world, y_world,z_world = xyz_world[0,:],xyz_world[1,:],xyz_world[2,:]
    lats_word, lons_word = xyz_to_ll(x_world,y_world,z_world)
    sat_ll_list = tuple(zip(list(lats_word),list(lons_word)))
    return sat_ll_list


def satellites_move(sat_ll, orbit_z_axis, velocity, time):
    lat_start, lon_start = sat_ll  # starting latitude and longitude
    assert (-90 <= lat_start <= 90 and -180 <= lon_start <= 180), "latitude must be from -90 to 90, longitude must be from -180 to 180"
    # alpha = z-axis latitude rotation, beta = z-ais longitude rotation
    # we assume that the satellite is moving around the arbitrary equator orbit
    # with a different z-axis
    alpha, beta = orbit_z_axis

    # transform lat, lon to x,y,z
    x1,y1,z1 = ll_to_xyz(lat_start,lon_start)
    # calculate rotation matrix for coordinates change
    rotation = rotation_matrix_with_angle(alpha, beta)
    # calculate latitude and longitude relative to rotation axis
    [x2,y2,z2] = rotation.dot(np.array([x1,y1,z1])).tolist()
    lat_middle,lon_middle = xyz_to_ll(x2,y2,z2)
    # apply velocity
    lon_middle += velocity*time
    x2,y2,z2 = ll_to_xyz(lat_middle,lon_middle)
    # transform the coordinate back to the original one
    [x1,y1,z1] = np.linalg.inv(rotation).dot(np.array([x2,y2,z2]))
    lat_end,lon_end = xyz_to_ll(x1,y1,z1)

    return lat_end,lon_end


if __name__ == "__main__":
    orbit_z_axis=(5,90)
    num_sats = 6
    sat_ll_list = init_satellites(orbit_z_axis,num_sats)
    print(sat_ll_list)

    for i,sat_ll in enumerate(sat_ll_list):
        new_lat,new_lon = satellites_move(sat_ll, orbit_z_axis, 20, 5)
        print(f"Satellite {i}: start_lat {sat_ll[0]} start_lon {sat_ll[1]} end_lat {new_lat} end_lon {new_lon}")
