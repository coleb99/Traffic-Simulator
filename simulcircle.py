# -*- coding: utf-8 -*-
"""
Created on Tue Apr 21 00:03:27 2026

@author: coleb
"""

import random #for random seeding of cars
import copy #for copying certain data for safety
import numpy as np #for vector math
import bisect #for efficient resorting during lane changes


class Car:
    def __init__(self,car_id,pos,vel,time_value,lane):
        self.id = car_id
        self.pos = pos #meters
        self.vel = vel #m/s
        self.time_value = time_value # ideal price per time saved
        self.lane = lane
        self.prev_lane = lane #for animation trickery
        self.lane_choice = lane
        self.time_since_switch = 0 #all cars must wait ~1s to switch at beginning
        self.color = color(time_value)
        
class Lane:
    def __init__(self,lane_id,price):
        self.cars=[]
        self.id=lane_id
        self.price=price #in $$ per unit meter
        self.positions=[]
        self.avg_speed=0
        self.revenue = 0

class Simulation:
    def __init__(self):
        self.avg_speed = 0
        self.revenue = 0
        
def setup(cfg,lanes,n_cars,express_price):
    #init sim
    sim = Simulation()
    #setup
    seed_cars(cfg,n_cars,lanes,lanes[0])
    n_lanes = len(lanes)
    express_lane = lanes[n_lanes-1]
    express_lane.price = express_price
    
def get_revenue(lanes):
    n_lanes = len(lanes)
    express_lane = lanes[n_lanes-1]
    return express_lane.revenue

def get_avg_speed(lanes,n_cars):
    #calculate individual lane speeds
    speeds,lane_weight = [],[]
    for lane in lanes:
        v_avg = lane.avg_speed*3.6 #in km/hr
        speeds.append(v_avg)
        lane_weight.append(len(lane.cars)/n_cars)
    #calculate average speed
    try:
        total_avg_speed = np.average(speeds,weights=lane_weight)
    except ZeroDivisionError:
        total_avg_speed = 0 
        
    return speeds, total_avg_speed
def update(car, next_car, lane, dt):
    if next_car == None:
        car.pos += car.vel * dt
        car.vel = min (car.vel + car.max_acc * dt, Car.vmax) 
    else:
        target_gap = Car.min_gap + Car.time_headway * next_car.vel
        gap = (next_car.pos - car.pos)%(Lane.length)
        
        '''required_stop_dist = car.vel**2 / (2 * Car.max_brake)#hard safety cap
        if required_stop_dist > gap:
                car.vel = max(0, car.vel - Car.max_brake * dt)'''
                
        #think of car velocity change to reach target like a spring!
        displacement = gap - target_gap
        rel_speed = car.vel - next_car.vel
        
        #if the car is too close, this emergency code kicks in
        predicted_gap = gap - rel_speed * dt
        safe_gap = predicted_gap - Car.min_gap
        if safe_gap < 0:
            car.vel = min(car.vel, next_car.vel)
        
        acc = Car.k1 * displacement - Car.k2 * rel_speed
        acc = max(min(acc ,Car.max_acc),-Car.max_brake)
        
        #update position
        delta_pos = car.vel * dt
        car.pos = car.pos + delta_pos
        
        lane.revenue += lane.price * delta_pos #collect revenue 
         
        #update velocity
        car.vel = max(0,min (car.vel + acc*dt,Car.vmax))
        


def update_all(lane,dt): # list of cars in lane
    if not lane.cars:
        pass
    else:
        #each car must update simulataneously without impacting each other
        copy_lane = [copy.deepcopy(car) for car in lane.cars]
        if len(copy_lane)==1:
            update(copy_lane[0],None,lane,dt)
        else:
            update(copy_lane[0],lane.cars[-1],lane,dt)#loops around
        for i in range(1,len(copy_lane)):
            update(copy_lane[i],lane.cars[i-1],lane,dt) #reference original lane
        for i in range(len(lane.cars)):#copy changes to original all at once
            lane.cars[i].pos,lane.cars[i].vel= copy_lane[i].pos,copy_lane[i].vel
        
        while lane.cars[0].pos>=Lane.length:#fix wraparound
            car = lane.cars[0]
            car.pos = car.pos % Lane.length
            lane.cars.remove(car)
            lane.cars.append(car)#moves car to back of list
    lane.positions = [car.pos for car in lane.cars]

def seed_cars(cfg,N,lanes,starting_lane): #all cars start spaced evenly on starting lane
    car_types=cfg["car_types"][0]
    weights = cfg["weights"][0]
    random_on = cfg["random_on"][0]
    
    if not random_on: #place cars equally separated
        for i,pos in enumerate(np.linspace(0,Lane.length,N, endpoint = False)):
            time_value = random.choices(car_types,weights = weights,k=1)[0]
            car = Car(i,pos,0,time_value,starting_lane)
            starting_lane.cars.append(car)
            starting_lane.positions.append(pos)
    else:
         pos = 0
         spacing = Lane.length/N
         if spacing < Car.min_gap: #too many cars to place randomly
             seed_cars(N,lanes,starting_lane, random_on=False)
             return
         for i in range(N): #each car random dist ahead up to separation
             pos = pos + Car.min_gap+random.random()*(spacing-Car.min_gap)
             time_value = random.choices(car_types,weights = weights,k=1)[0]
             car = Car(i,pos,0,time_value,starting_lane)
             starting_lane.cars.append(car)
   
def color(time_value):
    if not time_value:
        return 'cyan'
    if time_value==0.002:
        return 'blue'
    if time_value==0.005:
        return 'green'
    if time_value==0.015:
        return 'red'
      

def min_safe_dist(front_car,back_car):
    if front_car.vel >= back_car.vel:
        return Car.min_gap
    else:
        return (back_car.vel-front_car.vel)**2/(2*Car.max_acc)+Car.min_gap
        #on assumption that one can reasonably decelerate and still leave min_gap
        
def local_speed_ahead(car,new_lane):
    tau = Car.look_ahead_time
    min_look_ahead = Car.min_look_ahead_distance
    positions = new_lane.positions
    N=len(positions)
    cars = new_lane.cars
    
    if not cars:
        return Car.vmax

    # establish nearest cars ahead
    i = bisect.bisect_left([-p for p in positions],-car.pos)
    D = car.vel * tau + min_look_ahead
    v_list, weights = [],[]
    
    for step in range(N): #N is just a safety valve, will usually trigger early when gap>D
        new_car = cars[(i - 1 - step) % N]
        gap = (new_car.pos - car.pos) % Lane.length
        if gap<Car.min_gap: #don't count itself
            continue
        elif gap > D:#car too far ahead to be considered local
            break
        else:
            weight = 1 / gap
            v_list.append(new_car.vel)
            weights.append(weight)
    
    if not v_list:
        return Car.vmax
    else:
        return np.average(v_list, weights = weights)
    
def can_switch(car,new_lane):
    positions = new_lane.positions
    N = len(new_lane.cars)
    cars = new_lane.cars
    if not cars: #can always switch to empty lane
        return True
    
    #establish dist to nearest cars
    i = bisect.bisect_left([-p for p in positions],-car.pos) #largest index ahead of car
    car_behind = cars[i % N]
    car_ahead = cars[(i - 1) % N]
    if (car_ahead.pos - car.pos)%Lane.length > min_safe_dist(car_ahead,car):
        if (car.pos - car_behind.pos)%Lane.length > min_safe_dist(car,car_behind):
            return True
    return False

def switch_value(car,old_lane,new_lane): #in time/dist
    if old_lane == new_lane:
        return 0
    
    #determine speeds of each lane
    v_old = local_speed_ahead(car,old_lane)
    v_new = local_speed_ahead(car,new_lane)

    time_saved =  1/(v_old+1e-6) - 1/(v_new+1e-6) #cushion to avoid div0
    cost = new_lane.price - old_lane.price
    if car.time_value:
        return time_saved - cost/car.time_value - Car.switch_cost_base #base cost for switching
    else: #for those without money
        if new_lane.price: #never commit to lane with price
            return float('-inf')
        if old_lane.price: #if current lane has price
            return float('inf')
        else: 
            return time_saved - Car.switch_cost_base
            

def switch_choice(car,current,lanes):
    choices = [lane for lane in lanes if lane == current or can_switch(car,lane)]
    return max(choices, key = lambda x: switch_value(car,current,x))

def time_step(lanes,dt): #everything that happens in a time step
    n_lanes = len(lanes)
    #get data for visual updates
    for lane in lanes:
        if lane.cars:
            lane.avg_speed = np.average([car.vel for car in lane.cars])
        else:
            lane.avg_speed = 0
        
    #first allow switching
    moves = [set() for lane in lanes] #to keep track of which cars move
    
    #cars prepare to move
    for i in range(n_lanes):
        lane = lanes[i]
        left_lane = lanes[i-1] if i>0 else None
        right_lane = lanes[i+1] if i< n_lanes-1 else None
        lane_choices = [l for l in (lane, left_lane, right_lane) if l is not None] 
        #current lane first biases in tiebreaker
        
        for car in lane.cars:
            car.time_since_switch += dt
            if car.time_since_switch > Car.switch_cooldown:
                car.prev_lane = car.lane #no more lane-switch animation
                switch_chance = min(1/Car.switch_consider_time * dt,1)
                if random.random() < switch_chance: #random chance to switch each turn
                    
                    choice = switch_choice(car, lane, lane_choices)
                    if choice != lane:
                        car.lane_choice = choice
                        moves[i].add(car)
                    
    #cars actually move   
    for i in range(n_lanes):
        for car in moves[i]: #this is done all at once per lane to avoid cross-influence
            new_lane = car.lane_choice
            old_lane = car.lane
            if can_switch(car,new_lane): #best to check again, just to avoid crashes           
                new_lane.cars.append(car)
                old_lane.cars.remove(car)
                
                car.lane = new_lane
                car.time_since_switch = 0
    for lane in lanes:
        lane.cars.sort(key=lambda c: c.pos, reverse=True)
        lane.positions = [car.pos for car in lane.cars]
    
        
            
    #next, time updates within lanes   
    for lane in lanes:
        update_all(lane,dt)
        lane.positions = [car.pos for car in lane.cars]
        #this update always happens at the end of the step so the lanes are ordered in the output

def clear(lanes):#for resetting the sim
    for lane in lanes:
        lane.cars=[]
        
    


            
             



            

        
    
    
    
            


