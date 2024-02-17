# -*- coding: utf-8 -*-
"""
Created on Fri Feb 16 15:08:52 2024

@author: Jon :)
@tags: untagged,none
# How to use:

"""

# A board B is given as a 1x9 vector where B_i in [None,0,1] is player id.
# Boards use row-major indexing.
class Board:
    def __init__(self,a=None,pid=0):
        self.roundnum=1
        if not a:a=[None]*9
        else:
            self.roundnum=1
            for i in range(len(a)):
                if a[i]!=None: self.roundnum += 1
        self.a=a
        self.pid=pid
        self.djikstra={"cost":100,"winner":-1}
        self.binary=None
    
    # Reproduce from a sequence of moves ie [0,3,2...] (upto 9 items)
    def from_sequence(seq,pid0=0):
        b=Board(pid=pid0)
        for x in seq:
            if not b.place(x): return None # Invalid configuration
        return b
    def calculate_roundnum(binary):
        return binary.bit_count()-1
    # Create a sequence of moves that fit this board (not chronological)
    def to_sequence(self):
        p0=[] ; p1=[]
        num_rounds=0
        for i in range(len(self.a)):
            if self.a[i]==None: continue
            num_rounds += 1
            if self.a[i]==0: p0.append(i)
            else: p1.append(i)
        seq=[]
        pid0=0 if len(p0)>=len(p1) else 1
        for i in range(num_rounds):
            if pid0==0:
                seq.append(p0.pop())
                pid0=1
            else:
                seq.append(p1.pop())
                pid0=0
        return seq
    
    def isvalid(self):
        # Check if there are more pieces of one type than the other
        c0=0 ; c1=0
        for i in range(len(self.a)):
            if self.a[i]==0: c0 += 1
            if self.a[i]==1: c1 += 1
        if not (c0==c1 or c0==c1+1):
            return False
        
        # Check if there are more than one win conditions fulfilled
        wincons=0
        # Check rows
        for rowidx in range(3):
            pid=self.a[rowidx*3]
            if pid==None: continue
            winning=True
            for i in range(1,3):
                if self.a[rowidx*3+i]!=pid:
                    winning=False
                    break
            if winning: wincons+=1
        
        # Check columns
        for colidx in range(3):
            pid=self.a[colidx]
            if pid==None: continue
            winning=True
            for i in range(1,3):
                if self.a[colidx+i*3]!=pid:
                    winning=False
                    break
            if winning: wincons+=1
        
        # Check diagonals
        pid=self.a[0]
        if pid!=None:
            winning=True
            for i in range(1,3):
                if self.a[i*4]!=pid:
                    winning=False
                    break
            if winning: wincons+=1
            
        pid=self.a[2]
        if pid!=None:
            winning=True
            for i in range(1,3):
                if self.a[i*2+2]!=pid:
                    winning=False
                    break
            if winning: wincons+=1
        if wincons>1: return False
        return True
    
    def to_binary(self):
        num=0b11
        for i in range(len(self.a)):
            num <<= 2
            if self.a[i]==0: num += 0b01
            if self.a[i]==1: num += 0b10
        self.binary=num
        return num
    
    def from_binary(num):
        a=[None]*9
        b=Board(a) # <-- passed by reference so all is good :)
        b.binary=num
        c=8
        options=[None,0,1,None] # last item is for err safety
        while num>3:
            a[c]=options[num & 0b11]
            c -= 1
            num>>=2
        return b
            
    def countdiff(self,other):
        diffmask = self.to_binary() ^ other.to_binary()
        return diffmask.bit_count() # Count how many bits are set to 1
    
    def find_diff(self,other):
        for i in range(len(self.a)):
            if self.a[i]!=other.a[i]:
                return i
        return -1
        diffmask = self.to_binary() ^ other.to_binary()
        for i in range(len(self.a)):
            if diffmask & 3 == 0:
                diffmask>>=2
            else: return len(self.a)-1-i
        return -1
    
    
    # Win condition
    def winner(self):
        # Check rows
        for rowidx in range(3):
            pid=self.a[rowidx*3]
            if pid==None: continue
            winning=True
            for i in range(1,3):
                if self.a[rowidx*3+i]!=pid:
                    winning=False
                    break
            if winning:
                return pid
        
        # Check columns
        for colidx in range(3):
            pid=self.a[colidx]
            if pid==None: continue
            winning=True
            for i in range(1,3):
                if self.a[colidx+i*3]!=pid:
                    winning=False
                    break
            if winning:
                return pid
        
        # Check diagonals
        pid=self.a[0]
        if pid!=None:
            winning=True
            for i in range(1,3):
                if self.a[i*4]!=pid:
                    winning=False
                    break
            if winning:
                return pid
            
        pid=self.a[2]
        if pid!=None:
            winning=True
            for i in range(1,3):
                if self.a[i*2+2]!=pid:
                    winning=False
                    break
            if winning:
                return pid
    
    def __str__(self,players="XO"):
        b=self.a
        def f(a): return ". " if a==None else f"{players[a]} "
        return f"""
        +-------+
        | {f(b[0])}{f(b[1])}{f(b[2])}|
        | {f(b[3])}{f(b[4])}{f(b[5])}|
        | {f(b[6])}{f(b[7])}{f(b[8])}|
        +-------+"""
    def skip(self): # For debugging
        self.pid=1-self.pid
        self.roundnum += 1
    def place(self,i):
        if self.a[i]!=None: return False # Tile is already occupied
        self.a[i]=self.pid
        self.skip()
        return True
    def isfull(self):
        return self.roundnum>9
        for i in range(len(self.a)):
            if self.a[i]==None: return False
        return True
    def clone(self): return Board([a for a in self.a],self.pid)
    
    def first_empty(self):
        for i in range(len(self.a)):
            if self.a[i]==None:
                return i
        return -1
    def all_empty(self):
        res=[]
        for i in range(len(self.a)):
            if self.a[i]==None:
                res.append(i)
        return res
