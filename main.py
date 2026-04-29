# -*- coding: utf-8 -*-
"""
Created on Mon Apr 27 12:53:40 2026

@author: coleb
"""
import config as con
import simulcircle as sim 
import widgets as wid
import animation as ani

import matplotlib.pyplot as plt #for graphing
from matplotlib.animation import FuncAnimation #for doing the animation
from matplotlib.widgets import Slider, Button #for widgets on the animation
from collections import deque #for cleaning out old data as time passes

class SimState: #keeps track of a number of mutable simulation characteristics
    def __init__(self,config):
        con.apply_config(self,config)
        self.car_counter = self.n_cars
        

def main():
    #config
    config = con.setconfig('config.json')
    con.apply_config(sim.Lane,config["lane_attributes"])
    con.apply_config(sim.Car,config["car_attributes"])
    con.apply_config(SimState,config["constants"])
    state = SimState(config["sim_state_attributes"]) #sets n_cars
    spawn_cfg = config["car_time_value_dist"]
    
    #setup
    road_length= sim.Lane.length
    dt = 0.1
    revenue_stream = deque(maxlen=SimState.revenue_stream_memory+1) #keeps list at max length 31 (31-1=30s rolling window)
    lanes = [sim.Lane(i,0) for i in range(SimState.n_lanes-1)]
    express_lane = sim.Lane(SimState.n_lanes-1,1/1000*SimState.express_price)#convert price to per meter
    lanes.append(express_lane)

    #draw static elements
    fig, ax = plt.subplots(figsize = (12,3))
    plt.subplots_adjust(top=0.80,bottom=0.20)
    fig.suptitle("Flexible Price Express Lane Traffic Simulator")
    ani.draw_lanes(ax,lanes)
    scatter = ax.scatter([], [], s=state.n_cars)
    
    #draw data text bars
    lane_text = []
    for i,lane in enumerate(lanes):
        txt = ax.text(road_length*1.01, i+1,"Lane info",
                      ha='left',va='center') 
        lane_text.append(txt)
    head_text = ax.text(-road_length*0.01,SimState.n_lanes/2+0.5,"",ha='right', va='center')
    
    #gather items for animation
    metadata = [lanes,express_lane, state, revenue_stream,spawn_cfg]
    text = [head_text,lane_text]
    pending_actions = []
    
    #widgets
    #express_lane_price
    ax_slider = plt.axes([0.26, 0.9, 0.6, 0.03])
    slider = Slider(ax_slider, 'Express Price ($/km)', 0.0, 1.0, valinit=express_lane.price*1000)
    slider.on_changed(wid.make_update_price(express_lane, slider))
    #add car button
    ax_add = plt.axes([0.30, 0.03, 0.15, 0.07])
    btn_add = Button(ax_add, "Add Car")
    btn_add.on_clicked(lambda event: wid.spawn_car_request(event, pending_actions))
    #remove car button
    ax_remove = plt.axes([0.55, 0.03, 0.15, 0.07])
    btn_remove = Button(ax_remove, "Remove Car")
    btn_remove.on_clicked(lambda event: wid.remove_car_request(event, pending_actions))
    
    #initialize road with cars
    starting_lane = lanes[0]
    sim.seed_cars(spawn_cfg,state.n_cars, lanes, starting_lane)
    
    #run animation
    anim=FuncAnimation(
        fig,
        ani.animate,
        fargs = (scatter,metadata,text,pending_actions,dt),
        interval = dt * 1000, #1s
        blit = False,
        cache_frame_data = False)
    plt.show()
    
    #stop animation
    fig.canvas.mpl_connect('key_press_event', ani.on_key)


if __name__=="__main__":
    main()