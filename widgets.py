# -*- coding: utf-8 -*-
"""
Created on Mon Apr 27 15:15:08 2026

@author: coleb
"""
import simulcircle as sim 


import random #for spawning cars

def make_update_price(express_lane, slider):
    def update(val):
        express_lane.price = val / 1000 #convert from $/km to $/m in the code
    return update

def spawn_attempt(cfg,lanes,state):
    car_types=cfg["car_types"][0]
    weights = cfg["weights"][0]
    
    lane = lanes[0] #always spawn in lane 1
    i = state.car_counter
    
    if not lane.cars:
        vel = sim.Car.vmax
    else:
        lead = lane.cars[-1]
        vel = lead.vel
    pos = 0
    time_value = random.choices(car_types,weights = weights,k=1)[0]
    
    new_car = sim.Car(i,pos,vel,time_value,lane)
    
    if lane.positions[-1]>sim.Car.min_gap and lane.positions[0]<sim.Lane.length-sim.Car.min_gap:
        #if there is enough gap between forward and back cars to spawn a new one
        lane.cars.append(new_car)
        lane.positions.append(0)
        state.car_counter +=1
        state.n_cars +=1
        return True
    else:
        return False
    
def remove_car(lanes,state):
    if state.n_cars: #only remove a car if there is at least one car
        lane = random.choices(lanes,weights = [len(lane.cars) for lane in lanes],k=1)[0]
        car = random.choice(lane.cars)
        lane.positions.remove(car.pos)
        lane.cars.remove(car)
        state.n_cars -=1
        
def spawn_car_request(event,pending_actions):
    pending_actions.append("spawn")

def remove_car_request(event,pending_actions):
    pending_actions.append("remove")
    


    
    
