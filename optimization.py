# -*- coding: utf-8 -*-
"""
Created on Thu Apr 30 14:37:47 2026

@author: coleb
"""
import simulcircle as sim
import config as con

import random
import numpy as np

def eq_speed(n_lanes,m_cars,lane_type):
    if not m_cars:
        return sim.Car.vmax
    if lane_type == "standard":
        n = n_lanes - 1
    else:
        n = 1
    gap = sim.Lane.length * n / m_cars
    v = (gap - sim.Car.min_gap)/sim.Car.time_headway 
    return max(0,min(v,sim.Car.vmax))

def switch(car, current_lane,v_standard,v_express, p ):
    factor = 1 if current_lane == "standard" else -1 
    
    
    time_saved = factor*(1/(v_standard+1e-6) - 1/(v_express+1e-6))# cushion to avoid div0
    cost = factor * p*.001 #convert from $/km to $/m
    if car.time_value:
        switch_benefit =  time_saved - cost / car.time_value - sim.Car.switch_cost_base
        if switch_benefit > 0 :
            return True
        return False
    else: #no money, always chooses standard
        return False if current_lane == "standard" else True


def avg_speed(n_cars, m_express, v_standard, v_express):
    
    return (m_express * v_express + (n_cars - m_express)*v_standard)/n_cars

def opt_val(speed,rev):
    return rev
    
def set_up_cal(cfg,n_lanes,n_cars):
    car_types=cfg["car_types"][0]
    weights = cfg["weights"][0]
    #calculate exact number of each type of car
    amounts = [int(n_cars*weight) for weight in weights]
    time_values = []
    for j,amount in enumerate(amounts):
        for i in range(amount):
            time_values.append(car_types[j])
    #rounding error might remove a few cars, add them back
    while len(time_values)<n_cars:
        time_values.append(random.choices(car_types,weights = weights,k=1)[0])
    time_values.sort()
    #this is not a real lane in the animation, it is purely for calculation
    standard = [sim.Car(i,0,0,tv,"standard") for i,tv in enumerate(time_values)]
    m = 0 #initial number of cars in express
    v_standard = eq_speed(n_lanes, n_cars - m, "standard")
    v_express = eq_speed(n_lanes, m, "express")
    return standard, m, v_standard, v_express

def car_switch_block(n_lanes, n_cars, standard, price, data):
    m, v_standard, v_express = data
    next_car_up = standard[-1]#last car in standard has biggest time value
    if switch(next_car_up,"standard",v_standard,v_express,price):#opportunity to switch to paid
        v_standard2 = eq_speed(n_lanes, n_cars - (m+1), "standard")
        v_express2 = eq_speed(n_lanes, m+1, "express")
        if switch(next_car_up,"express",v_standard2,v_express2,price):#let them switch back if they want
            #average two equilibrium values
            switch_type = "double" #car swtiches and switches back
            v_p = 0.5*(avg_speed(n_cars,m,v_standard, v_express)+avg_speed(n_cars,m+1,v_standard2,v_express2))
            r_p = price* 0.5* (m * v_express + (m+1) * v_express2) 
            return switch_type, [v_p, r_p], [m,v_standard,v_express]
        else:
            switch_type = "single" #car switches once
            standard.pop(-1)
            return switch_type, [None, None], [m+1,v_standard2,v_express2]
    else:
        switch_type = "none" #car doesn't switch at all
        v_p = avg_speed(n_cars, m, v_standard, v_express)
        r_p = price * m * v_express
        return switch_type, [v_p, r_p], [m,v_standard, v_express]

def exp_val(cfg,n_lanes,n_cars,price):
    standard, m , v_standard, v_express = set_up_cal(cfg,n_lanes,n_cars)
    data = [m,v_standard,v_express]
    
    while data[0]<n_cars:
        switch_type, calc_vals, data =car_switch_block(n_lanes,n_cars,standard,price,data)
        if switch_type == "double" or switch_type == "none":
            return calc_vals
        elif switch_type == "single":
            continue
    #final values if loop never exited until the end
    m,v_standard,v_express = data
    v_p = avg_speed(n_cars,m, v_standard, v_express)
    r_p = price*m*v_express #convert to $/hr
    return v_p, r_p
    
    
def optimize(cfg,n_lanes,n_cars,pmax,sample_rate):
    price = pmax
    vals = {}
    standard, m , v_standard, v_express = set_up_cal(cfg,n_lanes,n_cars)
    data = m , v_standard, v_express
    while data[0]<n_cars and price>=0:
        switch_type, calc_vals, data =car_switch_block(n_lanes,n_cars,standard,price,data)
        if switch_type == "double" or switch_type == "none":
            vals[price] = opt_val(*calc_vals) #car chooses standard: express lane price too high
            price -= sample_rate
        elif switch_type == "single": #car chooses express, express lane not too high
            continue
        
    return max(vals, key = lambda x: vals[x])


    
        
    
    