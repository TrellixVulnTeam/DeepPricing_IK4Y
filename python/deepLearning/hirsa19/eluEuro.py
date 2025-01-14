import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import torchvision
from torch.utils.data import Dataset, DataLoader
import math
from torch.utils.data.sampler import SubsetRandomSampler
import matplotlib.pyplot as pyplot

# gradient computation etc. not efficient for whole data set
# -> divide dataset into small batches
# epoch = one forward and backward pass of ALL training samples
# batch_size = number of training samples used in one forward/backward pass
# number of iterations = number of passes, each pass (forward+backward) using [batch_size] number of sampes
# e.g : 100 samples, batch_size=20 -> 100/20=5 iterations for 1 epoch

# --> DataLoader can do the batch computation for us
# Implement a custom Dataset:
# inherit Dataset
# implement __init__ , __getitem__ , and __len__

class EuroParDataset(Dataset):
    def __init__(self, dataPath):
        # Initialize data, download, etc.
        xy = np.loadtxt(dataPath, delimiter=',', dtype=np.float32, skiprows=1)
        self.n_samples = xy.shape[0]
        # here the first column is the class label, the rest are the features
        self.x_data = torch.from_numpy(xy[:, 2:]) # size [n_samples, n_features]
        self.y_data = torch.from_numpy(xy[:, [1]]) # size [n_samples, 1]

    # support indexing such that dataset[i] can be used to get i-th sample
    def __getitem__(self, index):
        return self.x_data[index], self.y_data[index]

    # we can call len(dataset) to return the size
    def __len__(self):
        return self.n_samples


# create dataset
train_dataset = EuroParDataset("./deepLearning/hirsa19/data/mediumCEuroDataTrain.csv")
test_dataset = EuroParDataset("./deepLearning/hirsa19/data/mediumCEuroDataTest.csv")


# get first sample and unpack
first_data = train_dataset[0]
features, labels = first_data

#hyperparameters
n_features = len(features)
input_size = n_features

#hyperparameters
hidden_size1 = 120
hidden_size2 = 120
hidden_size3 = 120
outputSize = 1
num_epochs = 10
batchSize = 64
learning_rate = 0.01

# Load whole dataset with DataLoader
#use dataloader to effectice minibatching
train_loader = DataLoader(dataset=train_dataset,
                          batch_size=batchSize,
                          num_workers=2,
                          shuffle=True)

test_loader = DataLoader(dataset=test_dataset,
                               batch_size=batchSize, 
                               num_workers=2, 
                               shuffle=False)



#Design model
class NeuralNet(nn.Module):
    def __init__(self, input_size, hidden_size1, hidden_size2, hidden_size3, output_size):
        super(NeuralNet, self).__init__()
        self.input_size = input_size
        self.l1 = nn.Linear(input_size, hidden_size1)
        self.elu_1 = nn.ELU()
        self.l2 = nn.Linear(hidden_size1, hidden_size2)
        self.elu_2 = nn.ELU()
        self.l3 = nn.Linear(hidden_size2, hidden_size3)
        self.elu_3 = nn.ELU()
        self.l4 = nn.Linear(hidden_size3, outputSize)
        self.elu_4 = nn.ELU()
    
    def forward(self,x):
        out = self.l1(x)
        out = self.elu_1(out)
        out = self.l2(out)
        out = self.elu_2(out)
        out = self.l3(out)
        out = self.elu_3(out)
        out= self.l4(out)
        return out

model = NeuralNet(input_size, hidden_size1, hidden_size2, hidden_size3, outputSize)

#loss and optimizer
criterion = nn.MSELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

# Train the model
n_total_steps = len(train_loader)
#enumereate epoch
for epoch in range(num_epochs):
    epoch_loss = 0
    for i, (X, y) in enumerate(train_loader):  #one batch of samples       
        optimizer.zero_grad() # zero the gradient buffer

        #forward pass and loss
        y_predicted = model(X)
        loss = criterion(y_predicted,y)
        
        # Backward and optimize
        loss.backward()
        optimizer.step() #does weight update

        # accumulate loss
        epoch_loss += loss

    epoch_loss /= n_total_steps
    print (f'Epoch [{epoch+1}/{num_epochs}], Loss: {epoch_loss:.4f}')



##############
# Evaluate Model
###############
from numpy import vstack
from sklearn.metrics import mean_squared_error
model.eval()
predictions, actuals = list(), list()
for i, (inputs, targets) in enumerate(test_loader):
    # evaluate the model on the test set
    yhat = model(inputs)
    # retrieve numpy array
    yhat = yhat.detach().numpy()
    actual = targets.numpy()
    actual = actual.reshape((len(actual), 1))
    # store
    predictions.append(yhat)
    actuals.append(actual)
predictions, actuals = vstack(predictions), vstack(actuals)

#model performance
# calculate mse
from sklearn.metrics import r2_score
from sklearn.metrics import mean_absolute_error
mse = mean_squared_error(actuals, predictions)
print('MSE: %.6f, RMSE: %.6f' % (mse, np.sqrt(mse)))
print ('R Squared =',r2_score(actuals, predictions))
print ('MAE =',mean_absolute_error(actuals, predictions))

# Plot
def abline(slope, intercept):
    """Plot a line from slope and intercept"""
    axes = plt.gca()
    x_vals = np.array(axes.get_xlim())
    y_vals = intercept + slope * x_vals
    plt.plot(x_vals, y_vals, 'r--', linewidth=1)

import matplotlib.pyplot as plt
import matplotlib
from matplotlib import rcParams

rcParams['figure.figsize']=6,4
plt.scatter(predictions, actuals, alpha=0.5, s=1)
plt.xlabel("Predictions Price/Strike Price")
plt.ylabel("Actual Price/Strike Price")
plt.title("Multilayer Perceptrons Predictions Vs. Actual Targets")
#plt.legend(loc=2) #location of legend
plt.grid(True, color='k', linestyle=':') # make black grid and linestyle
plt.style.use('ggplot')
abline(1,0)
rcParams['agg.path.chunksize']=10**4
plt.savefig("/home/ppl/Documents/Universitet/KUKandidat/Speciale/DeepHedging/latex/Figures/PredictionEuroC.png")
plt.show()



############
# Make predictions
###########
# make a class prediction for one row of data
def predict(row, model):
    # convert row to data
    row = torch.tensor([row])
    # make prediction
    yhat = model(row)
    # retrieve numpy array
    yhat = yhat.detach().numpy()
    return yhat

row = [0.9,0.02, 0.5, 1]
yhat = predict(row, model)
print('Predicted: %.3f' % yhat)

    