import numpy as np
import networkx as nx

from MRP_interpolator import MRP_interpolator

class WP_MRP(MRP_interpolator):
    """
    Class for WP-MRP, extending MRP_interpolator

    Attributes
    ----------
    original_grid : 2D numpy array
        the original grid supplied to be interpolated
    pred_grid : 2D numpy array
        interpolated version of original_grid
    feature_grid : 3D numpy array
        grid corresponding to original_grid, with feature vectors on the z-axis
    G : networkx directed graph
        graph representation of pred_grid
    model : sklearn-based prediction model
        user-supplied machine learning model used to predict weights

    Methods
    -------
    run():
        Runs WP-MRP
        
    train():
        Train supplied prediction model on subsampled data or a training set
    """    
    
    def __init__(self,grid,feature_grid,model):
        # Feature grid is a 3d grid, where x and y correspond to grid, and the z axis contains feature
        # vectors
        
        self.original_grid = grid.copy()
        self.pred_grid = grid.copy()
        self.feature_grid = feature_grid.copy()
        self.model = model
        self.G = self.to_graph(grid)   
    
            
    def run(self,iterations):
        """
        Runs WP-MRP for the specified number of iterations.
        
        :param iterations: number of iterations used for the state value update function
        :returns: interpolated grid pred_grid
        """
        for n in self.G.nodes(data=True):
            r = n[1]['r']
            c = n[1]['c']
            y = n[1]['y']
            E = n[1]['E']
            
            if(np.isnan(y)):
                v_a_sum = 0
                for n1,n2,w in self.G.in_edges(n[0],data=True):
                    destination_node = self.G.nodes(data=True)[n1]
                    E_dest = destination_node['E']
                    r1 = self.G.nodes(data=True)[n1]['r']
                    c1 = self.G.nodes(data=True)[n1]['c']
                    r2 = self.G.nodes(data=True)[n2]['r']
                    c2 = self.G.nodes(data=True)[n2]['c']

                    f1 = self.feature_grid[r1,c1,:]
                    f2 = self.feature_grid[r2,c2,:]
                    f = np.concatenate((f1,f2))
                    f = f.reshape(1,len(f))
                    
                    v_a = self.model.predict(f)[0] * E_dest
                    v_a_sum += v_a
                E_new = v_a_sum / len(self.G.in_edges(n[0]))
                nx.set_node_attributes(self.G,{n[0]:E_new},'E')

            else:
                nx.set_node_attributes(self.G,{n[0]:y},'E')
        
        self.update_grid()
        return(self.pred_grid)
    
    
    def train(self,train_grid=None,train_features=None):
        """
        Trains WP-MRP's weight prediction model on either subsampled
        data from original_grid and feature_grid, or a user-supplied 
        training grid with corresponding features.
        
        :param train_grid: optional user-specified training grid
        :param train_features: optional user-specified training feature grid
        """
    
        if(train_grid == None):
            train_grid = self.original_grid.copy()
        if(train_features == None):
            train_features = self.feature_grid.copy()
        
        # Compute true weight for all neighbour pairs with known values        
        true_gamma = {}
        num_viable = 0

        for n1,n2 in self.G.edges():
            y1 = self.G.nodes(data=True)[n1]['y']
            y2 = self.G.nodes(data=True)[n2]['y']
            if(not(np.isnan(y1) or np.isnan(y2))):
                y1 = self.G.nodes(data=True)[n1]['y']
                y2 = self.G.nodes(data=True)[n2]['y']
                true_weight = y2 / max(0.01,y1)
                true_gamma[(n1,n2)] = true_weight
                num_viable += 1

        # Setup feature matrix and ground truth vector

        num_features = len(train_features[0][0]) * 2

        y = np.zeros(num_viable)
        X = np.zeros((num_viable,num_features))

        # Iterate over edges

        i = 0
        for n1,n2,a in self.G.edges(data=True):
            y1 = self.G.nodes(data=True)[n1]['y']
            y2 = self.G.nodes(data=True)[n2]['y']
            if(not(np.isnan(y1) or np.isnan(y2))):
                gamma = true_gamma[(n1,n2)]
                r1 = self.G.nodes(data=True)[n1]['r']
                c1 = self.G.nodes(data=True)[n1]['c']
                r2 = self.G.nodes(data=True)[n2]['r']
                c2 = self.G.nodes(data=True)[n2]['c']
                
                f1 = train_features[r1,c1,:]
                f2 = train_features[r2,c2,:]
                f = np.concatenate((f1,f2))

                # Set features
                X[i,:] = f
                # Set label
                y[i] = true_gamma[(n1,n2)]

                i += 1

        # Train model

        self.model.fit(X,y)