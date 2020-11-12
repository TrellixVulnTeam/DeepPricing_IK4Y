
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
import torch.nn as nn

####################
#Class for dataset
##################
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
###########################
#Model used for training
###########################
class NeuralNet(nn.Module):
    def __init__(self, input_size, hidden_size1, hidden_size2, hidden_size3, output_size):
        super(NeuralNet, self).__init__()
        self.input_size = input_size
        self.l1 = nn.Linear(input_size, hidden_size1)
        self.leaky_relu_1 = nn.LeakyReLU()
        self.l2 = nn.Linear(hidden_size1, hidden_size2)
        self.leaky_relu_2 = nn.LeakyReLU()
        self.l3 = nn.Linear(hidden_size2, hidden_size3)
        self.leaky_relu_3 = nn.LeakyReLU()
        self.l4 = nn.Linear(hidden_size3, outputSize)
        self.leaky_relu_4 = nn.LeakyReLU()
    
    def forward(self,x):
        out = self.l1(x)
        out = self.leaky_relu_1(out)
        out = self.l2(out)
        out = self.leaky_relu_2(out)
        out = self.l3(out)
        out = self.leaky_relu_3(out)
        out= self.l4(out)
        out = self.leaky_relu_4(out)
        return out
#####################
# get dataset
###################
datasets = ["./deepLearning/minAmerican/data1/60KUniInSampleAmeriMin.csv", "./deepLearning/minAmerican/data1/60KInMoneyAmerMin.csv","./deepLearning/minAmerican/data1/60KLongTAmeriMin.csv"]
test_dataset = EuroParDataset(datasets[2])
# get first sample and unpack
first_data = test_dataset[0]
features, labels = first_data

#Hyperparameters
batchSize = 64
n_samples, n_features = len(test_dataset), len(features)
input_size = n_features
hidden_size1 = 120
hidden_size2 = 120
hidden_size3 = 120
outputSize = 1

########################
#load trained model
###################
loaded_model = NeuralNet(n_features, hidden_size1, hidden_size2, hidden_size3, outputSize)
#for param in loaded_model.parameters():
#    print("without training model", param)
loaded_model.load_state_dict(torch.load("/home/ppl/Documents/Universitet/KUKandidat/Speciale/DeepPricing/python/deepLearning/Models/ModelAM_Min2.pth"))
loaded_model.eval()
#loaded_model.state_dict()
#for param in loaded_model.parameters():
#    print("loaded model", param)

##################
#load test data
##################
test_loader = DataLoader(dataset=test_dataset,
                               batch_size=batchSize, 
                               num_workers=2, 
                               shuffle=False)
##############
# Evaluate Model on test data
###############
from numpy import vstack
from sklearn.metrics import mean_squared_error
predictions, actuals = list(), list()
for i, (inputs, targets) in enumerate(test_loader):
    # evaluate the model on the test set
    yhat = loaded_model(inputs)
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
print ('R Squared = %.6f' % r2_score(actuals, predictions))
print ('MAE = %.6f' % mean_absolute_error(actuals, predictions))

# Plot
def abline(slope, intercept):
    """Plot a line from slope and intercept"""
    axes = plt.gca()
    x_vals = np.array(axes.get_xlim())
    y_vals = intercept + slope * x_vals
    plt.plot(x_vals, y_vals, 'c--', linewidth=1)

import matplotlib.pyplot as plt
import matplotlib
from matplotlib import rcParams

rcParams['figure.figsize']=5,4
plt.style.use('ggplot')
plt.scatter(predictions, actuals, alpha=0.5, s=1)
plt.xlabel("Predicted Price")
plt.ylabel("Actual Price")
plt.title("MLP Predictions Vs. Actual Targets")
#plt.legend(loc=2) #location of legend
#plt.grid(True, color='k', linestyle=':') # make black grid and linestyle
abline(1,0)
rcParams['agg.path.chunksize']=10**4
plt.savefig("/home/ppl/Documents/Universitet/KUKandidat/Speciale/DeepPricing/latex/Figures/longTAmerMinP.png")
plt.show()



############
# Make predictions
###########
# make a class prediction for one row of data
#def predict(row, model):
#    # convert row to data
#    row = torch.tensor([row])
#    # make prediction
#    yhat = model(row)
#    # retrieve numpy array
#    yhat = yhat.detach().numpy()
#    return yhat
#
#row = [0.9,0.02, 0.5, 1]
#yhat = predict(row, loaded_model)
#print('Predicted: %.3f' % yhat)

    