# -*- coding: utf-8 -*-
"""
Created on Thu Apr 23 10:39:51 2026

@author: coleb
"""
import simulcircle as sim
import optimization as opt
import widgets as wid

import numpy as np #for finding the average of lists and whatnot
import matplotlib.pyplot as plt #for graphing


def get_pos_and_color(lanes): #get location data for animation
    x = []
    y = []
    colors = []
    
    for lane_id, lane in enumerate(lanes):
        for car in lane.cars:
            x.append(car.pos) #x value is car's position
            #inter_dist allows cars to appear to travel between lanes
            inter_dist = (1-car.time_since_switch/sim.Car.switch_cooldown)*(car.prev_lane.id - car.lane.id)
            y.append(lane_id+1+inter_dist) #y value is lane
            colors.append(car.color)
    return x,y, colors

def draw_lanes(ax,lanes):
    for i in range(len(lanes)):
        ax.axhline(y=i+0.5, color='black', linestyle='-', linewidth=0.5, alpha=0.5)
        ax.axhline(y=i+1, color='gray', linestyle='--', linewidth=0.5, alpha=0.5)
        ax.set_ylim(0.5, len(lanes) + 0.5)
        ax.set_xlim(0, sim.Lane.length)
    plt.yticks([])#do not label lanes

def animate(frame,scatter,metadata,text,pending_actions,dt):
    lanes,express_lane,state, revenue_stream,spawn_cfg=metadata
    head_text,lane_text = text
    #enact actions
    new_pending_actions = []
    for action in pending_actions:
        if action=="spawn": #new spawn requests only
            success = wid.spawn_attempt(spawn_cfg,lanes,state)
            if not success:
                new_pending_actions.append(action) #adds to the queue for next time
        if action =="remove":
            wid.remove_car(lanes,state)
    pending_actions[:]= new_pending_actions
    
    #update simulation
    sim.time_step(lanes,dt)
    
    
    #update display
    x,y,colors = get_pos_and_color(lanes)
    scatter.set_offsets(np.column_stack((x,y)))
    scatter.set_color(colors)
    
    # update text every 1 second
    if frame % int(1 / dt) == 0:
        
        speeds, avg_speed = sim.get_avg_speed(lanes,state.n_cars)
        #individual lane text
        for lane, speed, txt in zip(lanes, speeds, lane_text):
            v_avg = speed
            price_per_km = lane.price*1000
            txt.set_text(f"{v_avg:.1f} km/hr\n\n${price_per_km:.2f} per km")
        
        #calculate average revenue
        total_revenue = sim.get_revenue(lanes)
        revenue_stream.append(total_revenue)
        rev_avg = (revenue_stream[-1]-revenue_stream[0])*3600/len(revenue_stream) #120 30-sec segments per hour
        
        #expected values
        if state.reset:
            exp_speed, exp_rev =opt.exp_val(spawn_cfg,len(lanes),state.n_cars,price = 1000*express_lane.price)
            state.exp_speed = exp_speed *3.6
            state.exp_rev = exp_rev *3.6
            state.reset=False
        head_text.set_text(f'total cars:\n{state.n_cars}\n\naverage speed:\n{avg_speed:.1f} km/hr\n\nexpected:\n{state.exp_speed:.1f} km/hr\n\nrevenue:\n${rev_avg:.2f}/hr\n\nexpected:\n${state.exp_rev:.2f}/hr')
    
    return (scatter,head_text,*lane_text)


    
def on_key(anim,event):
    if event.key == 'q':
        anim.event_source.stop()
        plt.close()


    
    
