"""
satellites movement simulation: Ting
"""
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
    sat_ll_list = [list(item) for item in zip(lats_word, lons_word)]
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


def earth_sat_distance(earth_lat, earth_lon, sat_lat, sat_lon):
    # according to the starlink blog, https://blog.apnic.net/2024/05/17/a-transport-protocols-view-of-starlink/
    # the height of a satellite is about 550km
    SAT_H = 550.
    EARTH_R = 6378.
    # calculate cartesian coordinates for earth station:
    x_earth = EARTH_R * np.cos(np.radians(earth_lat)) * np.cos(np.radians(earth_lon))
    y_earth = EARTH_R * np.cos(np.radians(earth_lat)) * np.sin(np.radians(earth_lon))
    z_earth = EARTH_R * np.sin(np.radians(earth_lon))
    # calculate cartesian coordinates for the satellite:
    sat_r = EARTH_R + SAT_H
    x_sat = sat_r * np.cos(np.radians(sat_lat)) * np.cos(np.radians(sat_lon))
    y_sat = sat_r * np.cos(np.radians(sat_lat)) * np.sin(np.radians(sat_lon))
    z_sat = sat_r * np.sin(np.radians(sat_lon))
    # calculate distance between earth and satellite
    distance = np.sqrt((x_sat - x_earth) ** 2 + (y_sat - y_earth) ** 2 + (z_sat - z_earth) ** 2)
    return distance


if __name__ == "__main__":
    orbit_z_axis=(5,90)
    num_sats = 6
    sat_ll_list = init_satellites(orbit_z_axis,num_sats)
    print(sat_ll_list)

    for i,sat_ll in enumerate(sat_ll_list):
        new_lat,new_lon = satellites_move(sat_ll, orbit_z_axis, 20, 5)
        print(f"Satellite {i}: start_lat {sat_ll[0]} start_lon {sat_ll[1]} end_lat {new_lat} end_lon {new_lon}")
