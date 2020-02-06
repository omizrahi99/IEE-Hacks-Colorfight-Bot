from colorfight import Colorfight
import time
import random
from colorfight.constants import BLD_GOLD_MINE, BLD_ENERGY_WELL, BLD_FORTRESS
from math import *

def distance(p1,p2):
    return fabs(p2[0]-p1[0]) + fabs(p2[1]-p1[1])


# Create a Colorfight Instance. This will be the object that you interact
# with.
game = Colorfight()

# Connect to the server. This will connect to the public room. If you want to
# join other rooms, you need to change the argument
game.connect(room = 'final')

# game.register should return True if succeed.
# As no duplicate usernames are allowed, a random integer string is appended
# to the example username. You don't need to do this, change the username
# to your ID.
# You need to set a password. For the example AI, the current time is used
# as the password. You should change it to something that will not change
# between runs so you can continue the game if disconnected.
if game.register(username = 'Code Koalas', \
        password = str(int(time.time()))):
    # This is the game loop
    

    while True:
        # The command list we will send to the server
        cmd_list = []
        # The list of cells that we want to attack
        my_attack_list = []
        # update_turn() is required to get the latest information from the
        # server. This will halt the program until it receives the updated
        # information.
        # After update_turn(), game object will be updated.
        game.update_turn()

        # Check if you exist in the game. If not, wait for the next round.
        # You may not appear immediately after you join. But you should be
        # in the game after one round.
        if game.me == None:
            continue

        me = game.me

                

        # game.me.cells is a dict, where the keys are Position and the values
        # are MapCell. Get all my cells.
        outer_cells = []
        boundary_cells = []
        cells_to_fortify = []
        for cell in game.me.cells.values():
            if cell.is_home:
                home = cell
            for pos in cell.position.get_surrounding_cardinals():
                c = game.game_map[pos]
                if c.owner != game.uid and c not in outer_cells:
                    outer_cells.append(c)
                    if c.owner != 0:
                        cells_to_fortify.append(cell)
                if c.owner != game.uid and cell not in boundary_cells:
                    boundary_cells.append(cell)

        if home.building.can_upgrade and home.building.upgrade_gold < me.gold and home.building.upgrade_energy < me.energy:
            cmd_list.append(game.upgrade(home.position))
            me.gold -= home.building.upgrade_gold
            me.energy -= home.building.upgrade_energy

        enemy_cells = []
        for cell in game.game_map.get_cells():
            if cell.owner != game.uid and cell.owner != 0:
                enemy_cells.append(cell)


        enemy_cell_positions = []
        for cell in enemy_cells:
            enemy_cell_positions.append((cell.position.x,cell.position.y))


        distance_from_enemy = []
        for cell in outer_cells:
            pt = (cell.position.x,cell.position.y)
            closest_enemy = min(enemy_cell_positions, key = lambda i: distance(pt,i))
            distance_from_enemy.append((distance(pt,closest_enemy),cell))
        distance_from_enemy.sort(key=lambda tup: -tup[0])
        cells_to_attack = [tup[1] for tup in distance_from_enemy]

        distance_from_enemy = []
        for cell in game.me.cells.values():
            if cell.building.is_empty:
                pt = (cell.position.x,cell.position.y)
                closest_enemy = min(enemy_cell_positions, key = lambda i: distance(pt,i))
                distance_from_enemy.append((distance(pt,closest_enemy),cell))
        distance_from_enemy.sort(key=lambda tup: -tup[0])
        cells_to_build = [tup[1] for tup in distance_from_enemy]
        cells_for_wells = cells_to_build[::2]
        cells_for_mines = cells_to_build[1::2]

        distance_from_enemy = []
        for cell in game.me.cells.values():
            if not cell.building.is_empty:
                pt = (cell.position.x,cell.position.y)
                closest_enemy = min(enemy_cell_positions, key = lambda i: distance(pt,i))
                distance_from_enemy.append((distance(pt,closest_enemy),cell))
        distance_from_enemy.sort(key=lambda tup: -tup[0])
        cells_to_upgrade = [tup[1] for tup in distance_from_enemy]


        print("cells to fortify:")
        for cell in cells_to_fortify:
            print((cell.position.x,cell.position.y))

        fortify_gold = (4*me.gold)//5
        if game.turn>400:
            fortify_gold = me.gold//3
        me.gold -= fortify_gold

        for cell in cells_to_fortify:
            if cell.building.is_empty and fortify_gold>=100:
                cmd_list.append(game.build(cell.position,BLD_FORTRESS))
                print("We built a fortress on ({}, {})".format(cell.position.x, cell.position.y))
                fortify_gold -= 100   

        for cell in cells_to_fortify:
            if cell.building.can_upgrade and \
                    cell.building.level < me.tech_level and \
                    cell.building.upgrade_gold < fortify_gold and \
                    cell.building.upgrade_energy < me.energy:
                cmd_list.append(game.upgrade(cell.position))
                print("We upgraded ({}, {})".format(cell.position.x, cell.position.y))
                fortify_gold   -= cell.building.upgrade_gold
                me.energy -= cell.building.upgrade_energy


        me.gold += fortify_gold


        spending_gold = me.gold
        if game.turn>300:
            spending_gold = me.gold//2
        if game.turn>400:
            spending_gold = me.gold//3

        wells_gold = spending_gold//2
        mines_gold = spending_gold//6
        gold_for_upgrading = spending_gold//3

        attack_energy = me.energy

        for cell in cells_to_upgrade:
            if cell.building.can_upgrade and \
                (cell.building.is_home or cell.building.level < me.tech_level) and \
                cell.building.upgrade_gold < gold_for_upgrading and \
                cell.building.upgrade_energy < me.energy:
                cmd_list.append(game.upgrade(cell.position))
                print("We upgraded ({}, {})".format(cell.position.x, cell.position.y))
                gold_for_upgrading   -= cell.building.upgrade_gold

        wells_gold += gold_for_upgrading

        mylist = [100,200,300,400,500,1000,2000,3000,4000,5000,10000000000]
        attacklist = []
        for i in mylist:
            for cell in cells_to_attack:
                if cell.attack_cost < attack_energy and cell.attack_cost < i and cell not in attacklist:
                    cmd_list.append(game.attack(cell.position,cell.attack_cost))
                    attack_energy -= cell.attack_cost
                    attacklist.append(cell)

        for cell in cells_for_wells:
            if wells_gold>100:
                cmd_list.append(game.build(cell.position,BLD_ENERGY_WELL))
                print("We built a well on ({}, {})".format(cell.position.x, cell.position.y))
                wells_gold -= 100

        for cell in cells_for_mines:
            if mines_gold>100:
                cmd_list.append(game.build(cell.position,BLD_GOLD_MINE))
                print("We built a mine on ({}, {})".format(cell.position.x, cell.position.y))
                mines_gold -= 100

                



        # Send the command list to the server
        result = game.send_cmd(cmd_list)
        print(result)
