# -*- coding: utf-8 -*-
"""
Created on Fri Feb 16 13:04:25 2024
@author: Jon :)
@tags: game

Minimax tic-tac-toe ;)
"""
 
from tictactoe_board import Board
import json, os # for baking results
import numpy as np # for silly laughter effect

class PlayerInst:
    def __init__(self,pid=0,name="Human"):
        self.pid=pid
        self.name=name
    def begin_turn(self,board):
        inp=input("Choose a tile [x,y]: ").replace('[','').replace(']','')
        if len(inp)==0:
            print("(Aborted)")
            return -1
        if ',' in inp:
            x,y=inp.split(',')
            i=int(x)+int(y)*3
            return i
        else:
            i=int(inp)
            return i


path_to_graph = 'graphWeighted.json'

if os.path.exists(path_to_graph):
    with open(path_to_graph, 'r') as f:
        data, graph = json.load(f)
else:
    # Generate the graph
    from itertools import product
    options = [None, 0, 1]
    boards=[]
    for comb in product(options, repeat=9): # 19683 combinations in total
        b=Board(comb)
        if b.isvalid():
            boards.append(b)
    print("Number of boards that can be made:",len(boards))
    
    # If there is exactly one bit in difference between the two boards,
    # there exists a move that takes us between them --> edge in our graph.
    bins=[b.to_binary() for b in boards] # binary is stored in b.binary ;)
    
    def bindiff(b1,b2): # Counts how many (b1 XOR b2) bits are set to 1
        return (b1^b2).bit_count()
    
    
    # uses binary representation as key. NOTE: graph is bidirectional to make
    # life simple in djikstra, but KEEP NOTE OF ROUNDNUM!!
    graph={}
    for b in bins:
        graph[b]=[]
    for i in range(len(bins)):
        for j in range(i+1,len(bins)):
            if bindiff(bins[i],bins[j])==1:
                graph[bins[i]].append(bins[j])
                graph[bins[j]].append(bins[i])
    data={b:{"cost0":100,"cost1":100} for b in bins}
    
    # debugging
    test_board=list(graph.keys())[100]
    print(f"{test_board} has {len(graph[test_board])} edges, including:")
    print(Board.from_binary(int(test_board)))
    print(Board.from_binary(graph[test_board][0]))
    
    # Mark winners and start djikstra
    frontier=[]
    for b in boards:
        winner=b.winner()
        if winner==None:continue
        node=data[b.binary]
        node[f"cost{winner}"]=0
        frontier.append(b.binary)
    
    while len(frontier)>0:
        newfront=[]
        for b in frontier:
            node0=data[b]
            newcost0 = node0["cost0"]+1
            newcost1 = node0["cost1"]+1
            for neighbor in graph[b]:
                if Board.calculate_roundnum(neighbor)>Board.calculate_roundnum(b):
                    continue
                node=data[neighbor]
                if newcost0<node["cost0"] or newcost1<node["cost1"]:
                    node["cost0"]=min(node["cost0"],newcost0)
                    node["cost1"]=min(node["cost1"],newcost1)
                    if neighbor not in newfront:
                        newfront.append(neighbor)
        frontier=newfront
        print(f"Front: {len(frontier)}")
        
    with open(path_to_graph,"w") as f:
        json.dump([data,graph],f)
    with open(path_to_graph, 'r') as f: # turn keys into strings cus im lazy lol
        data, graph = json.load(f)
        
    print("Completed!")
    
#---------- Bot helper functions :) ---------
def bot_choose(i):
    y,x=divmod(i,3)
    print(f"Chose: {x},{y}")
    return i
#--------------------------------------------

# Greedy bot will always move to reduce the cost left for its own victory ie lookahead=1
class GreedyBot:
    def __init__(self,pid=1,name="Greg"):
        self.pid=pid
        self.name=name
    def begin_turn(self,board):
        neighbors=graph[str(board.to_binary())]
        # The graph has bidir. edges, so we have to make sure we're going FORWARDS in roundnum not backwards
        adjacent_states=[n for n in neighbors if Board.calculate_roundnum(n)>board.roundnum]
        sortedmoves=sorted(adjacent_states,key=lambda n:data[str(n)][f"cost{self.pid}"])
        i=board.find_diff(Board.from_binary(sortedmoves[0]))
        return bot_choose(i)

# Maximin bot will minimize the maximum cost, lookahead=2 rounds
class MinimaxBot:
    def __init__(self,pid=1,name="Minny"):
        self.pid=pid
        self.name=name
    def begin_turn(self,board):
        if board.roundnum==1: return bot_choose(4) # Solid start
        min_maxcost=0
        best_n=None
        neighbors=graph[str(board.to_binary())]
        
        for n in neighbors:
            roundnum=Board.calculate_roundnum(n)
            if roundnum<board.roundnum:
                continue
            adjacent_states=[n for n in graph[str(n)] if Board.calculate_roundnum(n)>roundnum]
            if len(adjacent_states)==0: continue
            maxcost_n = max([data[str(n)][f"cost{self.pid}"]-data[str(n)][f"cost{1-self.pid}"] for n in adjacent_states])
            if maxcost_n<min_maxcost:
                min_maxcost=maxcost_n
                best_n=n
        if best_n==None:
            return bot_choose(board.first_empty())
        i=board.find_diff(Board.from_binary(best_n))
        return bot_choose(i)


def get_adjacent_states(binary):
    roundnum=Board.calculate_roundnum(binary)
    return [n for n in graph[str(binary)] if Board.calculate_roundnum(n)>roundnum]

# Optim bot will minimize the maximum cost, lookahead=end of game
# plays tic-tac-toe optimally
class OptimBot:
    def __init__(self,pid=1,name="Ophelia", lookahead=10):
        self.pid=pid
        self.name=name
        self.lookahead = lookahead
    def begin_turn(self, board):
        if board.roundnum==1: return bot_choose(4)
        _, best_state = self.minimax(board, self.lookahead, True)
        if best_state==None:
            return bot_choose(board.first_empty())
        i=board.find_diff(Board.from_binary(best_state))
        return bot_choose(i)
    
    # => min_eval, best_state
    def minimax(self, board, depth, is_maximizing_player):
        if depth == 0 or board.roundnum>=9:
            return self.evaluate(board), None

        best_state = None
        adjacent_states=get_adjacent_states(board.to_binary())
        if is_maximizing_player:
            max_eval = float('-inf')
            for option in adjacent_states:
                new_board = Board.from_binary(option)
                eval, _ = self.minimax(new_board, depth - 1, not is_maximizing_player)
                if eval > max_eval:
                    max_eval = eval
                    best_state = option
            return max_eval, best_state
        else:
            min_eval = float('inf')
            for option in adjacent_states:
                new_board = Board.from_binary(option)
                eval, _ = self.minimax(new_board, depth - 1, not is_maximizing_player)
                if eval < min_eval:
                    min_eval = eval
                    best_state = option
            return min_eval, best_state

    def evaluate(self, board):
        node=data[str(board.to_binary())]
        return node[f"cost{1-self.pid}"]-node[f"cost{self.pid}"]
    
    # Not implemented yet, should be a bit faster
    def evaluate_bin(self, binary):
        node=data[str(binary)]
        return node[f"cost{1-self.pid}"]-node[f"cost{self.pid}"]
    
# Bogus bot will play a random move
class BogusBot:
    def __init__(self,pid=1,name="Abogus"): # abogus?!
        self.pid=pid
        self.name=name
    def begin_turn(self,board):
        for _ in range(4):
            print(np.random.choice(["hi","hi","ha","he","ho"]),end="")
        print("!")
        return bot_choose(np.random.choice(board.all_empty()))

# Play the game!
players=[OptimBot(0),PlayerInst(1)]
#players=[PlayerInst(0,"P1"),PlayerInst(1,"P2")]
def play_game():
    b=Board()
    print("Playing tic-tac-toe for two :)")
    print(b)
    tries=0
    while not b.isfull() and b.winner()==None:
        print(f"Player {players[b.pid].name}'s turn.")
        i=players[b.pid].begin_turn(b)
        tries += 1
        if tries>=3:
            b.skip()
            print(f"Skipping {players[b.pid].name} >:(")
        if i<0: break
        if not b.place(i):
            print("This square is occupied :( Please choose another tile.")
        else:
            print(b)
            tries=0
    winner=b.winner()
    if winner==None: print("No winner.")
    else: print(f"{players[1-b.pid].name} won!")
    if 'y' in input("Play again? [y/n]: ").lower():
        return play_game()
    return b
b=play_game()
