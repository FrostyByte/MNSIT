import numpy as np
import tensorflow as tf #just to download data
from numba import njit
import matplotlib.pyplot as plt
import time
from itertools import repeat
class NN(object):
    def __init__(self,sizes):
        self.layers=len(sizes)
        self.sizes=sizes
        self.biases = [np.zeros(y) for y in sizes[1:]] # array of bases with y*1 arrays depth= two indices
        self.weights = [np.random.randn(y, x)/np.sqrt(x) for x, y in zip(sizes[:self.layers-1], sizes[1:])] # list of arrays of y*x size depth=3,first index= layer, second= row and 3rd=column
        self.velocity = [np.random.randn(y, x)/np.sqrt(x) for x, y in zip(sizes[:self.layers-1], sizes[1:])]
        (x, y),(x_t, y_t) = tf.keras.datasets.mnist.load_data()       #y is a 1d array of outputs with entries as integers ranging from 0 to 9
        l,l_t=len(x),len(x_t) 
        x,x_t=x.reshape(l,784)/255,x_t.reshape(l_t,784)/255         #Reshaping and scaling the input arrays to fit into the model
        kek,lol=np.zeros((l,10)),np.zeros((l_t,10))               # array of empty 1*10 arrays 
        for i in np.arange (l): kek[i][y[i]]=1                       # converting all the arrays such that the only the value on the index coresponding to the output is one.
        y=kek                                                   # this helps in cost calculation
        for i in np.arange(l_t): lol[i][y_t[i]]=1
        y_t=lol
        s=60                                                   #validation split
        x_v,y_v,x,y=x[0:l//s],y[0:l//s],x[l//s:],y[l//s:]
        self.train=[[x,y] for x,y in zip(x,y)]
        self.test=[[x,y] for x,y in zip(x_t,y_t)]
        self.valid=[[x,y]for x,y in zip(x_v,y_v)]
        self.tr_len,self.test_len,self.vl_len=len(self.train),len(self.test),len(self.valid)
        
    
    def random_divide_in_batches(self,train,n,batch_size):
        x=np.random.permutation(train)
        mini_batches = [x[k:k+batch_size] for k in np.arange(0, n,batch_size)]
        return mini_batches
    
    def train_model(self,train,n,epoch,batch_size,rate,test,reg_parameter=0,
                        fuck="sigma",cost='cross_entropy',regularization='L2',classification=True,
                        plot=False,stop_early=True,learn_schedule=True,momentum=0,metric="accuracy"): # x is at index one of each element of train 
        
        w,b,v=self.weights,self.biases,self.velocity
        cost_epoch,train_accuracy,test_accuracy=[],[],[]
        t0,i,max_acc,min_cost=time.time(),0,0,10000000
        while i<=epoch:
            x=self.random_divide_in_batches(train,n,batch_size) # list containing batches of training data
            for j in x:
                batch_size=len(j)
                out=list(map(self.operation,j,repeat(w),repeat(b),repeat(fuck)))
                c=self.cost(out,j,batch_size,cost)
                kost=c[0]+self.regularization(w,batch_size,regularization,reg_parameter)
                [Cb,Cw]=self.backprop(out,batch_size,w,c[1])
                [w,b]=self.update_parameters(w,b,v,Cw,Cb,rate,reg_parameter,batch_size,regularization,momentum)
            train_accuracy.append(self.accuracy(w,b,train,fuck,classification))
            test_accuracy.append(self.accuracy(w,b,test,fuck,classification))
            cost_epoch.append(c[0])
            est=((time.time()-t0)/(i+1))*(epoch-i-1)
            print('For epoch ',i+1,': rate={:.6f} cost={:.8f} train_accuracy= {:.3f} test accuracy= {:.2f} time left= {:.2f}'.format(rate,c[0],train_accuracy[i],test_accuracy[i],est),'s')
            
            if (max_acc<=test_accuracy[i] ):
                 max_acc,last_ten_mean=test_accuracy[i],np.mean(test_accuracy[i-9:i+1])
                 if(metric=="accuracy"): wbest,bbest=w,b
            if(min_cost>=cost_epoch[i] ):
                 min_cost=cost_epoch[i]
                 if(metric=="cost"):wbest,bbest=w,b
            if(i>=15 and learn_schedule==True):
                if(  metric=='accuracy' and (np.amax(test_accuracy[i-14:i+1])==test_accuracy[i-14])): rate=rate/2
                elif( metric=='cost' and np.amax(cost_epoc[i-19:i+1])==cost_epoch[i-19] ): rate=rate/2 
            if(stop_early==True and i>=25 and (np.amax(test_accuracy[i-24:i+1]))==test_accuracy[i-24]): break       # Stop early 

            #if((i+1)%5000==0):
                #if(input("Do you want to stop?")=="y"):break
            """elif(i+1%epoch==0):
                    if(input("Do you want to add extra epochs?")=='y'):
                        epoch+=input("Enter extra epochs")"""    
            
            i+=1
        print('Time elapsed: ',time.time()-t0,'Max_test_accuracy= ',max_acc,'Mean Last 10=',last_ten_mean,'min_Cost=',min_cost)
        
        if (plot==True):
            self.plot_graph(cost_epoch,train_accuracy,test_accuracy)
        
        
        return [wbest,bbest]
 
    def operation(self,i,w,b,fuck):                    #A is an array of all the n-D inputs, w= array of weights,b =array of biases
        y=[[i[0],np.zeros_like(i[0])]]                #list of all the outputs of every layer for 1 input, actual output of the network is at (layers-1)
        for j in np.arange(self.layers-1):
            x=self.activation(np.dot(w[j],y[j][0])+b[j],fuck)  #[0] for activation and[1] for derivative((sigma(z(l))))
            y.append(x) 
        return y
    
    def cost(self,out,train,n,func='quad'):              #outputs cost at index =0 and 
        c ,delta_last=0,[]
        if (func=='quad'):    
            for a,i in zip(out,train):
                d=a[self.layers-1][0]-i[1]
                c+=np.sum((d)**2)
                delta_last.append(d*a[self.layers-1][1])
            return [c/(2*n),delta_last]
        elif(func=='cross_entropy'):
            # A randomly choosen negligibily small constant, to be added within the log term to avoid any possibility of encountering log(0) 
            constant=0.0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001
            for a,i in zip(out,train):
                c+=np.sum((i[1]*np.log(a[self.layers-1][0]+constant))+(1-i[1])*np.log(1-a[self.layers-1][0]+constant))
                d=a[self.layers-1][0]-i[1]
                delta_last.append(d)
            return [-1*c/n,delta_last]
           
    def activation(self,x,func="sigma"): #0 for activation, 1 for differential
        a,d=0,0
        if(func=="sigma"):
            a= 1.0/(1.0+np.exp(-x))
            d= a*(1.0-a)
        elif(func=="relu"):
            d=np.zeros_like(x)
            a=np.maximum(x,d)
            d=np.where(a>d,1.,0.)
        elif(func=="tanh"):
            s=self.activation(2*x,func="sigma")
            a=2*s[0]-1
            d=4*s[1]
        elif(func=='softmax'):
            x=x/np.sum(x)
        return [a,d]
           
    def update_parameters(self,w,b,v,Cw,Cb,rate,t,n,regularization,momentum=0):
        reg=(rate*t)/n
        for i in np.arange(self.layers-1):
            v[i]=v[i]*momentum-rate*Cw[i]
            if (regularization=='L2'):
                w[i]+=v[i]-reg*w[i]
            elif(regularization=='L1'):
                w[i]+=v[i]-reg*np.sign(w[i])
            b[i]-=rate*Cb[i+1]
        return [w,b]
    def dropout(self,t,w,b):
        for layer in self.sizes[1:self.layers-1]:
            a=3

    
    def regularization(self,w,n,typ,t):
        s=0
        if(t==0): return 0
        if(typ=='L2'):
            for i in w: s+=np.sum(i**2)
            return t*s/(2*n)
        elif(typ=='L1'):   
            for i in w: s+=np.sum(np.abs(i))
            return (t*s)/n
    


    def backprop(self,out,n,w,delta_last): #Gives Cb and Cw ,n is the number of samples or mini batch size
        delta_all,Cw_all=[],[]
        for i in np.arange(n):
            delta_l,Cw=[None]*self.layers,[None]*(self.layers-1)
            delta_l[self.layers-1]=delta_last[i]
            if(i==0):
                for j in np.arange(self.layers-1,0,-1): #ulta iteration through layers,starting layer tak jana hi nahi isiliye 0
                    delta_l[j-1]=np.dot(w[j-1].transpose(),delta_l[j])*out[i][j-1][1]
                    Cw[j-1]=delta_l[j].reshape((len(delta_l[j]),1))*out[i][j-1][0]
                delta_all,Cw_all=delta_l,Cw
                
            else:
                delta_all[self.layers-1]+=delta_last[i]
                for j in np.arange(self.layers-1,0,-1): #ulta iteration through layers,starting layer tak jana hi nahi isiliye 0
                    delta_l[j-1]=np.dot(w[j-1].transpose(),delta_l[j])*out[i][j-1][1]
                    Cw_all[j-1]+=delta_l[j].reshape((len(delta_l[j]),1))*out[i][j-1][0]
                    delta_all[j-1]+=delta_l[j-1]
        return [delta_all,Cw_all]
        
    def evaluate(self,w,b,x,fuck,classification=True):
        for j in np.arange(self.layers-1):
            x=self.activation(np.dot(w[j],x)+b[j],fuck)[0]  #[0] for activation and[1] for derivative((sigma(z(l))))
        if(classification==True):return np.argmax(x)
        else: return x[0]

    def accuracy(self,w,b,test,fuck,classification):
        score,n=0,len(test)
        for k in test:
            if classification==True:
                if(self.evaluate(w,b,k[0],fuck,True)==np.argmax(k[1])): score+=1
            elif classification=='single':
                e=self.evaluate(w,b,k[0],fuck,False)
                if((e>0.5 and k[1][0]==1) or (e<0.5 and k[1][0]==0)): score+=1    
            else:
                score+=1-np.abs(self.evaluate(w,b,k[0],fuck,False)-k[1][0])/k[1][0]
        acc=((score/n)*100)    
        return acc

    def plot_graph(self,cost,train_acc,test_acc):
        fig,ax1=plt.subplots()
        ax1.set_xlabel('Epochs')
        ax1.set_ylabel('cost')
        ax1.plot(cost,color='tab:red')
        ax1.tick_params(axis='y',labelcolor='tab:red')
        ax2=ax1.twinx()
        ax2.set_ylabel('accuracy')
        ax2.plot(test_acc,color="tab:blue",label='test')
        ax2.plot(train_acc,color="tab:green",label='train')
        ax2.tick_params(axis='y',labelcolor="tab:blue")
        ax2.legend()
        fig.tight_layout()
        plt.show()          
        
            
        
