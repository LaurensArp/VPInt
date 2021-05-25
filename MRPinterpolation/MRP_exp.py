"""Module for MRP-based interpolation.
"""

import numpy as np
import networkx as nx
import datetime

class MRP:
    """
    Basic MRP class containing common functionality of SMRP and STMRP.

    Attributes
    ----------
    original_grid : 2D numpy array
        the original grid supplied to be interpolated
    pred_grid : 2D numpy array
        interpolated version of original_grid
    _dims : the number of dimensions for this MRP (2 for spatial, 3 for temporal)

    Methods
    -------
    reset():
        Returns pred_grid and G to their original state
        
    get_pred_grid():
        Returns pred_grid
        
    mean_absolute_error():
        Computes the mean absolute error of pred_grid compared to a given ground truth grid
    """
    
    def __init__(self,grid,init_strategy='zero'):
        self.original_grid = grid.copy()
        self.dims = len(grid.shape)
        self.init_pred_grid(init_strategy=init_strategy)
        
        
    def __str__(self):
        return(str(self.pred_grid))
    
    
    def reset(self):
        """Return prediction grid and graph representation to their original form"""
        self.pred_grid = self.original_grid
          
    
    def init_pred_grid(self,init_strategy='zero'):
        """Initialise pred_grid with mean values as initial values for missing cells
        
        :param init_strategy: method for initialising unknown values. Options: 'zero', 'random', 'mean'"""
        
        self.pred_grid = self.original_grid.copy()
        height = self.pred_grid.shape[0]
        if(self.dims > 1):
            width = self.pred_grid.shape[1]
        if(self.dims == 3):
            depth = self.pred_grid.shape[2]

        for i in range(0,height):
            if(self.dims > 1):
                for j in range(0,width):
                    if(self.dims == 3):
                        # Spatio-temporal case
                        for t in range(0,depth):
                            if(np.isnan(self.pred_grid[i,j,t])):
                                initval = 0
                                if(init_strategy == "random"):
                                    mean = np.nanmean(self.original_grid)
                                    std = np.nanstd(self.original_grid)
                                    initval = np.random.normal(mean,std)
                                elif(init_strategy == "mean"):
                                    initval = np.nanmean(self.original_grid)
                                self.pred_grid[i,j,t] = initval
                    else:
                        # Spatial case
                        if(np.isnan(self.pred_grid[i,j])):
                            initval = 0
                            if(init_strategy == "random"):
                                mean = np.nanmean(self.original_grid)
                                std = np.nanstd(self.original_grid)
                                initval = np.random.normal(mean,std)
                            elif(init_strategy == "mean"):
                                initval = np.nanmean(self.original_grid)
                            self.pred_grid[i,j] = initval
                        
            else:
                # Temporal case
                if(np.isnan(self.pred_grid[i])):
                    initval = 0
                    if(init_strategy == "random"):
                        mean = np.nanmean(self.original_grid)
                        std = np.nanstd(self.original_grid)
                        initval = np.random.normal(mean,std)
                    elif(init_strategy == "mean"):
                        initval = np.nanmean(self.original_grid)
                    self.pred_grid[i] = initval
             
               
    def get_pred_grid(self):
        """Return pred_grid"""
        self.update_grid()
        return(self.pred_grid)
           
    
    def r_squared(self,true_grid):
        """
        Compute the r^2 of pred_grid given true_grid as ground truth
        
        :param true_grid: ground truth for all grid cells
        :returns: r^2
        """
        height = self.pred_grid.shape[0]
        width = self.pred_grid.shape[1]
        if(self.dims == 3):
            depth = self.pred_grid.shape[2]
        
        m = np.mean(true_grid)
        
        res = 0
        tot = 0

        for i in range(0,height):
            for j in range(0,width):
                if(self.dims == 3):
                    # Spatio-temporal
                    for t in range(0,depth):
                        if(np.isnan(self.original_grid[i][j][t])):
                            resval = (true_grid[i][j][t] - self.pred_grid[i][j][t])**2
                            totval = (true_grid[i][j][t] - m)**2

                            res += resval
                            tot += totval

                else:
                    # Spatial/temporal
                    if(np.isnan(self.original_grid[i][j])):
                        resval = (true_grid[i][j] - self.pred_grid[i][j])**2
                        totval = (true_grid[i][j] - m)**2

                        res += resval
                        tot += totval
        r_squared = 1 - (res/tot)
            
        return(r_squared)
    

class SMRP(MRP):
    """
    Basic class implementing basic functions used by SD-MRP and WP-MRP.

    Attributes
    ----------
    original_grid : 2D numpy array
        the original grid supplied to be interpolated
    pred_grid : 2D numpy array
        interpolated version of original_grid

    Methods
    -------
    reset():
        Returns pred_grid to its original state
        
    get_pred_grid():
        Returns pred_grid
    """
    
    def __init__(self,grid,init_strategy='zero'):
        super().__init__(grid,init_strategy=init_strategy)
    
    
    def mean_absolute_error(self,true_grid,scale_factor=1,gridded=False):
        """
        Compute the mean absolute error of pred_grid given true_grid as ground truth
        
        :param true_grid: ground truth for all grid cells
        :param gridded: optional Boolean specifying whether to return an error grid with the MAE
        :returns: mean absolute error, optionally a tuple of MAE and per-cell error
        """
        
        # Rescale; naive approach for now
        
        
        height = self.pred_grid.shape[0]
        width = self.pred_grid.shape[1]
        
        new_height = int(height/scale_factor)
        new_width = int(width/scale_factor)
        
        new_pred_grid = self.pred_grid.copy().reshape((new_height,int(height/new_height),new_width,int(width/new_width))).sum(3).sum(1)
        new_original_grid = self.original_grid.copy().reshape((new_height,int(height/new_height),new_width,int(width/new_width))).sum(3).sum(1)
        new_true_grid = true_grid.copy().reshape((new_height,int(height/new_height),width,int(new_width/new_width))).sum(3).sum(1)
        error_grid = np.zeros((new_height,new_width))
        
        e = 0
        c = 0
              
        for i in range(0,new_height):
            for j in range(0,new_width):
                
                if(np.isnan(new_original_grid[i][j])):
                    err = abs(new_pred_grid[i][j] - new_true_grid[i][j])
                    error_grid[i][j] = err
                    e += err
                    c += 1
                else:
                    error_grid[i][j] = 0
        mae = e/c
        if(gridded):
            result = (mae,error_grid)
        else:
            result = mae
            
        return(result)

            
            
class STMRP(MRP):
    """
    Basic class implementing the basic spatio-temporal framework for 
    SD-MRP and WP-MRP.

    Attributes
    ----------
    original_grid : 3D numpy array
        the original grid supplied to be interpolated
    pred_grid : 3D numpy array
        interpolated version of original_grid
    true_time_indices : list of integers
        list containing the indices (temporal dimension) of pred_grid provided in the input data 

    Methods
    -------
    reset():
        Returns pred_grid and G to their original state
        
    dim_check():
        Checks the dimensions of supplied grid, transforms to
        3D grid if necessary
        
    set_timesteps():
        Automatically creates a 3D grid from a time-stamped
        dictionary of 2D spatial grids
        
    get_pred_grid():
        Returns pred_grid
    """

    def __init__(self,data,auto_timesteps,init_strategy='zero'):       
        if(auto_timesteps):
            new_grid = self.set_timesteps(data.copy())
        else:
            new_grid = self.dim_check(data.copy())
            
        super().__init__(new_grid,init_strategy=init_strategy)
           
    def dim_check(self,grid):
        """
        Checks the dimensions of the supplied grid, and transforms
        it into a 3D grid (at a single time step) if necessary (this
        retains non-temporal spatial MRP functionality).
        
        :param grid: grid to check dimensions of
        :returns: suitable 3D grid
        """
        dims = grid.shape
        if(grid.ndim == 1):
            new_grid = np.zeros((dims[0],1,1))
            new_grid[:,0,0] = grid
        elif(grid.ndim == 2):
            new_grid = np.zeros((dims[0],dims[1],1))
            new_grid[:,:,0] = grid
        elif(grid.ndim == 3):
            new_grid = grid
        return(new_grid)
    
    
    def set_timesteps(self,data):
        """
        Checks the dimensions of the supplied grid, and transforms
        it into a 3D grid (at a single time step) if necessary (this
        retains non-temporal spatial MRP functionality).
        
        :param data: dictionary containing time stamps as keys and
        2D spatial grids as values. Time stamps MUST be chronologically
        ordered, and in string format "YYYY-MM-DD HH:MM:SS"
        :returns: spatio-temporal 3D grid
        """
        
        stamps = []
        min_stamp = None
        max_stamp = None
        min_gap = None
        i = 0
        for k,v in data.items():
            time_obj = datetime.datetime.strptime(k,"%Y-%m-%d %H:%M:%S")
            stamps.append(time_obj)
            if(i > 0):
                diff = time_obj - stamps[i-1]
                if(min_gap != None):
                    if(diff < min_gap):
                        min_gap = diff
                else:
                    min_gap = diff
                max_stamp = time_obj
                
            else:
                min_stamp = time_obj
                max_stamp = time_obj
            
            i += 1
        
        # Create empty 3D grid with (max-min)/gap time steps incremented by gap
        
        str_ind = min_stamp.strftime("%Y-%m-%d %H:%M:%S")
        height = data[str_ind].shape[0]
        width = data[str_ind].shape[1]
        depth = int((max_stamp - min_stamp) / min_gap) + 1
        
        grid = np.empty((height,width,depth))
        grid[:] = np.nan
        
        # Assign 2D grids to appropriate time steps
        
        self.true_time_indices = []
        for k,v in data.items():
            stamp = datetime.datetime.strptime(k,"%Y-%m-%d %H:%M:%S")
            ind = int((stamp - min_stamp) / min_gap)
            grid[:,:,ind] = v
            self.true_time_indices.append(ind)
        
        # Return 3D grid
        
        return(grid)
    
    
    def mean_absolute_error(self,true_grid,gridded=False):
        """
        Compute the mean absolute error of pred_grid given true_grid as ground truth
        
        :param true_grid: ground truth for all grid cells
        :param gridded: optional Boolean specifying whether to return an error grid with the MAE
        :returns: mean absolute error, optionally a tuple of MAE and per-cell error
        """
        height = self.pred_grid.shape[0]
        width = self.pred_grid.shape[1]
        if(self.dims == 3):
            depth = self.pred_grid.shape[2]
            error_grid = np.zeros((height,width,depth))
        else:
            error_grid = np.zeros((height,width))
        
        e = 0
        c = 0
        for i in range(0,height):
            for j in range(0,width):
                if(self.dims == 3):
                    # Spatio-temporal
                    for t in range(0,depth):
                        if(t in self.true_time_indices):
                            if(np.isnan(self.original_grid[i][j][t])):
                                err = abs(self.pred_grid[i][j][t] - true_grid[i][j][t])
                                error_grid[i][j][t] = err
                                e += err
                                c += 1
                            else:
                                error_grid[i][j][t] = np.nan
                else:
                    # Spatial/temporal
                    if(np.isnan(self.original_grid[i][j])):
                        err = abs(self.pred_grid[i][j] - true_grid[i][j])
                        error_grid[i][j] = err
                        e += err
                        c += 1
                    else:
                        error_grid[i][j] = np.nan
        mae = e/c
        if(gridded):
            result = (mae,error_grid)
        else:
            result = mae
            
        return(result)
    
    
    def mean_absolute_error2(self,true_grid,gridded=False):
        """
        Compute the mean absolute error of pred_grid given true_grid as ground truth
        
        :param true_grid: ground truth for all grid cells
        :param gridded: optional Boolean specifying whether to return an error grid with the MAE
        :returns: mean absolute error, optionally a tuple of MAE and per-cell error
        """
        height = self.pred_grid.shape[0]
        width = self.pred_grid.shape[1]
        if(self.dims == 3):
            depth = self.pred_grid.shape[2]
            error_grid = np.zeros((height,width,depth))
        else:
            error_grid = np.zeros((height,width))
        
        e = 0
        c = 0
        for i in range(0,height):
            for j in range(0,width):
                # Spatio-temporal
                for t in range(0,depth):
                    if(np.isnan(self.original_grid[i][j][t])):
                        err = abs(self.pred_grid[i][j][t] - true_grid[i][j][t])
                        error_grid[i][j][t] = err
                        e += err
                        c += 1
                    else:
                        error_grid[i][j][t] = np.nan

        mae = e/c
        if(gridded):
            result = (mae,error_grid)
        else:
            result = mae
            
        return(result)