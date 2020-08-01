import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
import simPathStock

#Variables for american put
spot=36
r=0.06
vol=0.2
timePointsYear=50
T=1
n= 10**3
strike = 40  

#stockMatrix
from longstaff_schwartz.algorithm import longstaff_schwartz
from longstaff_schwartz.stochastic_process import GeometricBrownianMotion

# Model parameters
t = np.linspace(0, 1, 50)  # timegrid for simulation
r = 0.06  # riskless rate
sigma = 0.2  # annual volatility of underlying
n = 10**3  # number of simulated paths

# Simulate the underlying
gbm = GeometricBrownianMotion(mu=r, sigma=sigma)
rnd = np.random.RandomState(1234)
stockMatrix = 36 * gbm.simulate(t, n, rnd)  # x.shape == (t.size, n)


#contract function
putCall = lambda S, K: K-S if (K > S) else 0 

#Intrinsic matrix
def intrinsic(spot, timePointsYear, strike, T, n, stockMatrix):
    """ Finds the intrinsic value matrix """
    timePoints = T * timePointsYear
    intrinsicM = np.zeros((n, timePoints+1))
    count=1
    for timePoint in reversed(stockMatrix.T):
        intrinsicRow = [putCall(S, strike) for S in timePoint]
        intrinsicM[:,-count] = intrinsicRow
        count+=1
    return intrinsicM


#regression
def design(X, choice):
    if choice==1:
        "Design Matrix for linear regression"""
        basis1 = np.exp(-X/2)
        basis2 = np.exp(-X/2)*(1-X)
        basis3 = np.exp(-X/2)*(1-2*X+X**2/2)
        cov = np.concatenate((basis1, basis2, basis3)).T
    elif choice==2:
        """Design Matrix for linear regression"""
        basis1 = X
        basis2 = X**2
        cov = np.concatenate((basis1, basis2)).T
    else:
        choice = input("You entered an invalid choice for a basis, please enter 1 or 2")
        return design(X, choice)
    return cov

#cashflow matrix
def cashflow(spot, r, vol, timePointsYear, strike, T, n, choice, stockMatrix):
    """Calculate the cashflow matrix based on the optimal stopping rule by lsm algorithm"""
    timePoints = T * timePointsYear
    intrinsicM = intrinsic(spot, timePointsYear, strike, T, n, stockMatrix)
    #Watch out for changed dimension of cashflow and stoppingRule
    cashFlow = np.zeros((n, timePoints))
    stoppingRule = np.zeros((n, timePoints))
    
    count = 1 # number of timesteps taken (remember backward induction, hence starting at 1)
    for timePoint in reversed(stockMatrix.T):
        if (count == 1):
            stoppingRule[:, -count] = 1
            cashFlow[:, -count] = intrinsicM[:, -count] 
        elif (count == timePoints+1):
            #can only exercise after initiazation of option
            break
        else:
            intrinsicColumn = intrinsicM[:, -count]
            X = np.array([timePoint[intrinsicColumn>0]])
            numInMoney = np.sum(intrinsicColumn>0) #number of in money paths
            Y = np.zeros(numInMoney)
            index = 0
            for i in range(len(timePoint)):
                if (intrinsicColumn[i]>0):
                    for k in range(timePoints-count+1, timePoints):
                        if stoppingRule[i,k]==1:
                            Y[index] = cashFlow[i,k]*np.exp(-r*(k-(timePoints-count+1)))
                            index +=1
                else:
                    pass
            #TODO:look here, I think X and Y is right now
            designM = design(X, choice)
            lin_reg=LinearRegression()
            regPar = lin_reg.fit(designM,Y) 
            condExp = regPar.intercept_ + np.matmul(designM, regPar.coef_)
            intrinsicVal = intrinsicColumn[intrinsicColumn>0] 
            q = -1 # q counter
            for j in range(len(intrinsicColumn)):
                if (intrinsicColumn[j]>0):
                    q+=1
                    if (condExp[q] <= intrinsicVal[q]):
                        stoppingRule[j, timePoints - count] = 1
                        cashFlow[j, timePoints - count] = intrinsicColumn[j]
                        for k in range(count-1):
                            stoppingRule[j, timePoints-(count-1)+k]=0
                            cashFlow[j, timePoints-(count-1)+k]=0
        count+=1  
    
    return (cashFlow)

cashFlowMatrix = cashflow(spot, r, vol, timePointsYear, strike, T, n, 1, stockMatrix)

def findPV(r, cashFlowMatrix, timePointsYear):
    """Find present value of a cashflow matrix starting at 1. timestep"""
    PV = 0
    timeSteps = 1/timePointsYear
    for i in range(cashFlowMatrix.shape[0]):
        for j in range(cashFlowMatrix.shape[1]):
            PV += cashFlowMatrix[i,j]*np.exp(-r*((j+1)*timeSteps))
    return (PV/cashFlowMatrix.shape[0])
    
print(findPV(r, cashFlowMatrix, timePointsYear))



