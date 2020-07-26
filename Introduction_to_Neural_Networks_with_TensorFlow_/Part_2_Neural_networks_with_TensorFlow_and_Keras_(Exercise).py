#!/usr/bin/env python
# coding: utf-8

# # Neural Networks with TensorFlow and Keras
# 
# Deep neural networks tend to be massive with dozens or even hundreds of layers, that's where the term "deep" comes from. You can build one of these deep networks using only weight matrices as we did in the previous notebook, but in general it's very cumbersome and difficult to implement. TensorFlow has a nice API called **Keras** that provides a nice way to efficiently build large neural networks.

# ## Import Resources

# In[1]:


import warnings
warnings.filterwarnings('ignore')


# In[2]:


get_ipython().run_line_magic('matplotlib', 'inline')
get_ipython().run_line_magic('config', "InlineBackend.figure_format = 'retina'")

import numpy as np
import matplotlib.pyplot as plt

import tensorflow as tf
import tensorflow_datasets as tfds
tfds.disable_progress_bar()


# In[3]:


import logging
logger = tf.get_logger()
logger.setLevel(logging.ERROR)


# In[4]:


print('Using:')
print('\t\u2022 TensorFlow version:', tf.__version__)
print('\t\u2022 tf.keras version:', tf.keras.__version__)
print('\t\u2022 Running on GPU' if tf.test.is_gpu_available() else '\t\u2022 GPU device not found. Running on CPU')


# ## Load the Dataset

# Now we're going to build a larger network that can solve a (formerly) difficult problem, identifying text in an image. Here we'll use the MNIST dataset which consists of greyscale handwritten digits. Each image is 28x28 pixels, you can see a sample below
# 
# <img src='assets/mnist.png'>
# 
# Our goal is to build a neural network that can take one of these images and predict the digit in the image.
# 
# First up, we need to get the dataset we are going to use to train and test our Neural Network. We will get our dataset using the [`tensorflow_datasets`](https://www.tensorflow.org/datasets) package. TensorFlow Datasets is a repository of datasets ready to use with TensorFlow. TensorFlow Datasets has a wide variety of datasets to train your machine learning models for many different tasks, ranging from text to video. For a full list of the datasets available in TensorFlow Datasets check out the [TensorFlow Datasets Catalog](https://www.tensorflow.org/datasets/catalog/overview#all_datasets).
# 
# 
# The code below will load the MNIST dataset. 

# In[5]:


# Load training data
training_set, dataset_info = tfds.load('mnist', split = 'train', as_supervised = True, with_info = True)


# ## Inspect the Dataset

# We have loaded the training data into `training_set` and loaded dataset information into `dataset_info`.  Let's get the total number of classes and the total number of images in our training set from `dataset_info`.

# In[6]:


num_classes = dataset_info.features['label'].num_classes
print('There are {:,} classes in our dataset'.format(num_classes))

num_training_examples = dataset_info.splits['train'].num_examples
print('\nThere are {:,} images in the training set'.format(num_training_examples))


# We can use `training_set` as an iterator so, we can use the following statement to loop through the dataset:
# 
# ```python
# for image, label in training_set:
#     ## do things with images and labels
# ```
# 
# Let's print the shape and dtype of our images and labels. We'll use the `.take(1)` method to only choose one element from our dataset. Since our dataset consists of images, the `.take(1)` method will choose only one image. 

# In[7]:


for image, label in training_set.take(1):
    print('The images in the training set have:')
    print('\u2022 dtype:', image.dtype) 
    print('\u2022 shape:', image.shape)
  
    print('\nThe labels of the images have:')
    print('\u2022 dtype:', label.dtype) 


# The images in our dataset are tensors of `shape = (28, 28, 1)` and `dtype = uint8`. `unit8` represents an 8-bit unsigned integer and can hold integers in the range 0 to 255. On the other hand, the labels of our images are tensors of `dtype = int64`, which means they are 64-bit signed integers. Now let's see what an image from our dataset looks like. In order to plot our images, we will have to convert them from TensorFlow tensors to NumPy ndarrays first, by using the `.numpy()` method. Since the images have `shape = (28, 28, 1)` we will use the `.squeeze()` method to reshape the images to have `shape = (28, 28)`. The `.squeeze()` method removes single-dimensional entries from the shape of an ndarray.

# In[8]:


for image, label in training_set.take(1):
    image = image.numpy().squeeze()
    label = label.numpy()
    
# Plot the image
plt.imshow(image, cmap = plt.cm.binary)
plt.colorbar()
plt.show()

print('The label of this image is:', label)


# ## Create Pipeline

# As we can see, the pixel values of our images are in the range `[0, 255]`. We will now normalize the images and create a pipeline with our training set so that it can be fed into our neural network. In order to normalize the images we are going to divide the pixel values by 255. We will therefore, first change the `dtype` of our image from `uint8` to `float32`  (32-bit single-precision floating-point numbers) using the `tf.cast` function.

# In[9]:


def normalize(image, label):
    image = tf.cast(image, tf.float32)
    image /= 255
    return image, label

batch_size = 64

training_batches = training_set.cache().shuffle(num_training_examples//4).batch(batch_size).map(normalize).prefetch(1)


# You'll notice we created the pipeline with a batch size of `64`, and that we are shuffling our dataset. The batch size is the number of images we get in one iteration and are passed through our network, often called a *batch*. The `shuffle` transformation randomly shuffles the elements of our dataset before being fed to our network.
# 
# Although many of these transformations are commutative, the ordering of certain transformations has performance implications. For more information on these transformations and their impact on performance make sure to check the following links:
# 
# * [Pipeline Performance](https://www.tensorflow.org/beta/guide/data_performance)
# 
# 
# * [Transformations](https://www.tensorflow.org/api_docs/python/tf/data/Dataset)
# 
# Now that we have our `training_batches` let's inspect them:

# In[10]:


for image_batch, label_batch in training_batches.take(1):
    print('The images in each batch have:')
    print('\u2022 dtype:', image_batch.dtype) 
    print('\u2022 shape:', image_batch.shape)
  
    print('\nThere are a total of {} image labels in this batch:'.format(label_batch.numpy().size))
    print(label_batch.numpy())


# Now, let's see how we can grab a single image from our one of our batches.

# In[11]:


# Take a single batch of images, and remove the color dimension by squeezing it
for image_batch, label_batch in training_batches.take(1):
    images = image_batch.numpy().squeeze()
    labels = label_batch.numpy()

# Plot the image
plt.imshow(images[0], cmap = plt.cm.binary)
plt.colorbar()
plt.show()

print('The label of this image is:', labels[0])


# ## Build a Simple Neural Network
# 
# First, let's try to build a simple network for this dataset using weight matrices and matrix multiplications, just like we did in the previous notebook. Then, we'll see how to do it using TensorFlow and Keras, which provides a much more convenient and powerful method for defining network architectures.
# 
# The networks you've seen so far are called *fully-connected* or *dense* networks. Each unit in one layer is connected to each unit in the next layer. In fully-connected networks, the input to each layer must be a one-dimensional vector (which can be stacked into a 2D tensor as a batch of multiple examples). However, our images are 28 $\times$ 28 2D tensors, so we need to convert them into 1D vectors. Thinking about sizes, we need to convert the batch of images with shape `(64, 28, 28, 1)` to a have a shape of `(64, 784)`, 784 is 28 times 28. This is typically called *flattening*, we flattened the 2D images into 1D vectors.
# 
# In the previous notebook, you built a network with one output unit. Here we need 10 output units, one for each digit. We want our network to predict the digit shown in an image, so what we'll do, is calculate the probabilities that the image is of any one digit or class. This ends up being a discrete probability distribution over the classes (digits) that tells us the most likely class for the image. That means we need 10 output units for the 10 classes (digits). We'll see how to convert the network output into a probability distribution next.
# 
# > **Exercise:** Flatten the batch of images `images` that we've created above. Then build a simple network with 784 input units, 256 hidden units, and 10 output units using random tensors for the weights and biases. For now, use a sigmoid activation function for the units in the hidden layer. Leave the output layer without an activation, we'll add one that gives us a probability distribution next. **HINT:** You can use the [`tf.reshape()`](https://www.tensorflow.org/versions/r2.0/api_docs/python/tf/reshape) function to flatten the batch of images.

# In[12]:


## Solution
def activation(x):
    """ Sigmoid activation function
    
        Arguments
        ---------
        x: tf.Tensor. Must be one of the following types: bfloat16, half, float32, float64, complex64, complex128.
    """
    return 1/(1+tf.exp(-x))

# Flatten the input images
inputs = tf.reshape(images, [images.shape[0], -1])

# Print the shape of the inputs. Should be (64,784)
print('The inputs have shape:', inputs.shape)

# Create Neural Network parameters
w1 = tf.random.normal((784,256))
b1 = tf.random.normal((1,256))

w2 = tf.random.normal((256,10))
b2 = tf.random.normal((1,10))

# Perform matrix multiplications for the hidden layer
# and apply activation function
h = activation(tf.matmul(inputs, w1) + b1)

# Perform matrix multiplication for the output layer
output = tf.matmul(h, w2) + b2

# Print the shape of the output. It should be (64,10)
print('The output has shape:', output.shape)


# Now we have 10 outputs for our network. We want to pass in an image to our network and get out a probability distribution over the classes that tells us the most likely class(es) the image belongs to. Something that looks like this:
# <img src='assets/image_distribution.png' width=500px>
# 
# Here we see that the probability for each class is roughly the same. This is representing an untrained network, it hasn't seen any data yet so it just returns a uniform distribution with equal probabilities for each class.
# 
# To calculate this probability distribution, we often use the [**softmax** function](https://en.wikipedia.org/wiki/Softmax_function). Mathematically this looks like
# 
# $$
# \Large \sigma(x_i) = \cfrac{e^{x_i}}{\sum_k^K{e^{x_k}}}
# $$
# 
# What this does is squish each input $x_i$ between 0 and 1 and normalizes the values to give you a proper probability distribution where the probabilities sum up to one.
# 
# > **Exercise:** Implement a function `softmax` that performs the softmax calculation and returns probability distributions for each example in the batch. Note that you'll need to pay attention to the shapes when doing this. If you have a tensor `a` with shape `(64, 10)` and a tensor `b` with shape `(64,)`, doing `a/b` will give you an error because TensorFlow will try to do the division across the columns (called broadcasting) but you'll get a size mismatch. The way to think about this is the following: for each of the 64 examples, you only want to divide by one value, the sum in the denominator. So you need `b` to have a shape of `(64, 1)`. This way TensorFlow will divide the 10 values in each row of `a` by the one value in each row of `b`. Pay attention to how you take the sum as well. You'll need to define the `axis` keyword in `tf.reduce_sum()`. Setting `axis=0` takes the sum across the rows while `axis=1` takes the sum across the columns. You will also need to use the `keepdims` keyword in `tf.reduce_sum()` to make sure the output tensor has the correct shape `(64,1)`.

# In[13]:


## Solution
def softmax(x):
    """ Softmax function
    
        Arguments
        ---------
        x: tf.Tensor. Must be one of the following types: bfloat16, half, float32, float64, complex64, complex128.
    """
    
    return tf.exp(x) / tf.reduce_sum(tf.exp(x), axis = 1, keepdims = True)



# Apply softmax to the output
probabilities = softmax(output)

# Print the shape of the probabilities. Should be (64, 10).
print('The probabilities have shape:', probabilities.shape, '\n')


# The sum of probabilities for each of the 64 images should be 1
sum_all_prob = tf.reduce_sum(probabilities, axis = 1).numpy()

# Print the sum of the probabilities for each image.
for i, prob_sum in enumerate(sum_all_prob):
    print('Sum of probabilities for Image {}: {:.1f}'.format(i+1, prob_sum))


# ## Building Neural Networks with TensorFlow and Keras
# 
# Keras is a high-level API to build and train neural networks. `tf.keras` is TensorFlow's implementation of the Keras API. In Keras, deep learning models are constructed by connecting configurable building blocks called **layers**. The most common type of model is a stack of layers called a **Sequential** model. The model is called sequential because it allows a tensor to be passed sequentially through the operations in each layer. In TensorFlow, the sequential model is implemented with `tf.keras.Sequential`. 
# 
# In the cell below, we will use a Keras sequential model to build the same fully-connected neural network that we built in the previous section. Our sequential model will have three layers:
# 
# * **Input Layer:** `tf.keras.layers.Flatten` — This layer flattens the images by transforming a 2d-array of 28 $\times$ 28 pixels, to a 1d-array of 784 pixels (28 $\times$ 28 = 784). The first layer in a Sequential model needs to know the shape of the input tensors to the model. Since, this is our first layer, we need to specify the shape of our input tensors using the `input_shape` argument. The `input_shape` is specified using a tuple that contains the size of our images and the number of color channels. It is important to note that we don't have to include the batch size in the tuple. The tuple can have integers or `None` entries, where `None` entries indicate that any positive integer may be expected.
# 
# * **Hidden Layer:** `tf.keras.layers.Dense` — A fully-connected (also known as densely connected) layer. For this layer we need to specify the number of neurons (or nodes) we want to use and the activation function. Note that we don't have to specify the shape of the input tensor to this layer, since Keras performs automatic shape inference for all layers except for the first layer. In this particular case, we are going to use `256` neurons with a `sigmoid` activation fucntion. 
# 
# * **Output Layer:** `tf.keras.layers.Dense` — A fully-connected layer with 10 neurons and a *softmax* activation function. The output values will represent the probability that the image is a particular digit. The sum of all the 10 nodes values is 1.

# In[14]:


model = tf.keras.Sequential([
        tf.keras.layers.Flatten(input_shape = (28,28,1)),
        tf.keras.layers.Dense(256, activation = 'sigmoid'),
        tf.keras.layers.Dense(10, activation = 'softmax')
])

model.summary()


# ### Your Turn to Build a Neural Network
# 
# <img src="assets/mlp_mnist.png" width=600px>
# 
# > **Exercise:** Create a network with 784 input units, a hidden layer with 128 units and a ReLU activation, then a hidden layer with 64 units and a ReLU activation, and finally an output layer with 10 units and a softmax activation function. You can use a ReLU activation function by setting `activation = 'relu'`.

# In[15]:


## Solution
my_model_1 =  tf.keras.Sequential([
             tf.keras.layers.Flatten(input_shape = (28,28,1)),
             tf.keras.layers.Dense(128, activation = 'relu'),
             tf.keras.layers.Dense(64, activation = 'relu'),
             tf.keras.layers.Dense(10, activation = 'softmax')
])


my_model_1.summary()


# ## Activation Functions
# 
# So far we've only been looking at the softmax activation, but in general any function can be used as an activation function. The only requirement is that for a network to approximate a non-linear function, the activation functions must be non-linear. Here are a few more examples of common activation functions: Tanh (hyperbolic tangent), and ReLU (rectified linear unit).
# 
# <img src="assets/activation.png" width=700px>
# 
# In practice, the ReLU function is used almost exclusively as the activation function for hidden layers.

# ## Looking at the Weights and Biases
# 
# Keras automatically initializes the weights and biases. The weights and biases are tensors attached to each of the layers you defined in your model. We can get all the weights and biases from our model by using the `get_weights` method. The `get_weights` method returns a list of all the weight and bias tensors in our model as NumPy arrays.

# In[16]:


model_weights_biases = model.get_weights()

print(type(model_weights_biases))


# In[17]:


print('\nThere are {:,} NumPy ndarrays in our list\n'.format(len(model_weights_biases)))

print(model_weights_biases)


# We can also get the weights and biases for a specific layer by using the `get_layer` method. In this case we first specify the layer we want by using the `index` argument and the apply the `get_weights` method as we did before. For example, to get the weights and biases of the first layer of our sequential model we will use:
# 
# ```python
# weights = model.get_layer(index=0).get_weights()[0]
# biases = model.get_layer(index=0).get_weights()[1]
# 
# ```
# 
# Notice, that we used `index=0` to get the first layer of our model which in this case is a `tf.keras.layers.Flatten`. Since this layer just flattens our input, it has no weights or biases. Therefore, in this case, the layer with `index=0` has no weights or biases, so calling `get_weights()[0]` will produce an error because  `get_weights()` will return an empty list (`[]`). So, when you are getting the weights and biases from each layer you should check first whether the layer has any weights or biases at all. 
# 
# Alternatively, you can also use the `layers` method to get a list of the layers of your model. You can then loop through the layers and check if they have weights before calling `get_weights()`. Let's see an example:

# In[18]:


# Dislay the layers in our model
model.layers


# In[19]:


for i, layer in enumerate(model.layers):
    
    if len(layer.get_weights()) > 0:
        w = layer.get_weights()[0]
        b = layer.get_weights()[1]
        
        print('\nLayer {}: {}\n'.format(i, layer.name))
        print('\u2022 Weights:\n', w)
        print('\n\u2022 Biases:\n', b)
        print('\nThis layer has a total of {:,} weights and {:,} biases'.format(w.size, b.size))
        print('\n------------------------')
    
    else:
        print('\nLayer {}: {}\n'.format(i, layer.name))
        print('This layer has no weights or biases.')
        print('\n------------------------')


# As we can see, by default, all the biases are initialized to zero.
# 
# On the other hand, by default, the weights are initialized using a Glorot uniform initializer that draws samples from a uniform distribution within \[-`limit`, `limit`\] where `limit` is `sqrt(6 / (fan_in + fan_out))` where `fan_in` is the number of input units in the weight tensor and `fan_out` is the number of output units in the weight tensor.
# 
# In Keras, you can change the default initialization methods for the weights and biases. To know more about the available initializers check out the links below:
# 
# * [Available initializers](https://keras.io/initializers/)
# 
# * [Dense Layer](https://www.tensorflow.org/versions/r2.0/api_docs/python/tf/keras/layers/Dense)

# ## Make Predictions
# 
# To make predictions on a batch of images with our model we use the `.predict(image_batch)` method. This method takes the images in our batch, feeds them to our network, performs a forward pass, and outputs a NumPy ndarray of shape `(batch_size, num_classes)` with the predicted probabilities for each image in the batch. 
# 
# Since we have 64 images per batch (*i.e.* `batch_size = 64`) and our dataset has 10 classes (*i.e.* `num_classes = 10`), then our model will output an array of shape `(64,10)`. The rows in this array hold the predicted probabilities for our images. Consequently, the first row holds the predicted probabilities for the first image in our batch; the second row holds the predicted probabilities for the second image in our batch; the third row holds the predicted probabilities for the third image in our batch; and so on. In this case, the predicted probabilities consist of 10 values, that is, one probability per class. Therefore, for each of the 64 images in our batch we will have 10 probabilities. 
# 
# Let's plot our model's predicted probabilities for the first image in our batch.

# In[20]:


for image_batch, label_batch in training_batches.take(1):
    ps = model.predict(image_batch)
    first_image = image_batch.numpy().squeeze()[0]


fig, (ax1, ax2) = plt.subplots(figsize=(6,9), ncols=2)
ax1.imshow(first_image, cmap = plt.cm.binary)
ax1.axis('off')
ax2.barh(np.arange(10), ps[0])
ax2.set_aspect(0.1)
ax2.set_yticks(np.arange(10))
ax2.set_yticklabels(np.arange(10))
ax2.set_title('Class Probability')
ax2.set_xlim(0, 1.1)
plt.tight_layout()


# As you can see above, our model gives every digit roughly the same probability. This means our network has basically no idea what the digit in the image is. This is because we haven't trained our model yet, so all the weights are random!

# ## Subclassing with TensorFlow and Keras
# 
# The `tf.keras.Sequential` model is a simple stack of layers that cannot be used to create arbitrary models. Luckily, `tf.keras` gives us the flexibility to build fully-customizable models by subclassing the `tf.keras.Model` and defining our own forward pass.
# 
# In the following example we will use a subclassed `tf.keras.Model` to build the same neural network as we built above with 784 inputs, 256 hidden units, and 10 output units. As before, we will use a ReLu activation function for the units in the hidden layer, and a Softmax activation function for the output neurons. 

# In[21]:


class Network(tf.keras.Model):
    def __init__(self, num_classes = 2):
        super().__init__()
        self.num_classes = num_classes
    
        # Define layers 
        self.input_layer = tf.keras.layers.Flatten()
        self.hidden_layer = tf.keras.layers.Dense(256, activation = 'relu')
        self.output_layer = tf.keras.layers.Dense(self.num_classes, activation = 'softmax')
    
    # Define forward Pass   
    def call(self, input_tensor):
        x = self.input_layer(input_tensor)
        x = self.hidden_layer(x)
        x = self.output_layer(x)
    
        return x 


# Let's go through this bit by bit.
# 
# ```python
# class Network(tf.keras.Model):
# ```
# 
# Here we're inheriting from `tf.keras.Model`. Combined with `super().__init__()` this creates a class that provides a lot of useful methods and attributes. It is mandatory to inherit from `tf.keras.Model` when you're creating a class for your network. However, the name of the class itself can be anything.
# 
# We then create the layers of our network in the `__init__` method and set them as attributes of the class instance. We also assign the number of neurons in our output layer in the `__init__` method via the `num_classes` argument, which by default will have a value of 2.
# 
# ```python
# self.input = tf.keras.layers.Flatten()
# ```
# 
# The first layer flattens the input image as we have discussed previously. We have given this layer the name `self.input`. We will use this name to reference this layer later. It doesn't matter what name you give your layers, you can name them whatever you want.
# 
# ```python
# self.hidden = tf.keras.layers.Dense(256, activation = 'relu')
# ```
# 
# The second layer is a fully-connected (dense) layer with 256 neurons and a ReLu activation function. We have given this layer the name `self.hidden`. We will use this name to reference this layer later.
# 
# ```python
# self.output = tf.keras.layers.Dense(self.num_classes, activation = 'softmax')
# ```
# 
# The third and last layer (output layer) is also a fully-connected (dense) layer with `self.num_classes` neurons and a softmax activation function. By default the number of output units will be 2, but can be defined to be any other integer depending on the number of output classes of your dataset. 
# 
# Next, we define the forward pass in the `call` method.
# 
# ```python
# def call(self, input_tensor):
# ```
# 
# TensorFlow models created with `tf.keras.Model` must have a `call` method defined. In the `call` method we take `input_tensor` and pass it through the layers we defined in the `__init__` method.
# 
# ```python
# x = self.input(input_tensor)
# x = self.hidden(x)
# x = self.output(x)
# ```
# 
# Here the `input_tensor` is passed through each layer and reassigned to `x`. We can see that the `input_tensor` goes through the `input` layer, then the `hidden` layer, and finally through the `output` layer. The order in which you define the layers in the `__init__` method doesn't matter, but you'll need to sequence the layers correctly in the `call` method. Notice that we are referring to each layer in the `__init__` method by the name we gave them. Remember this names are arbitrary.
# 
# Now that we have defined our model class we can create a `model` object. Note that we didn't specify the shape of our input tensor in our `Network` class. In this case, the weights and biases will only be initialized when we build our model by calling `build(batch_input_shape)` or when the first call to a training/evaluation method (such as `.fit` or `.evaluate`) is made. We call this a delayed-build pattern.
# 
# So, now let's create a `model` object and build it (i.e. initialize its weights and biases) by calling `build()`.

# In[22]:


# Create a model object
subclassed_model = Network(10)

# Build the model, i.e. initialize the model's weights and biases
subclassed_model.build((None, 28, 28, 1))

subclassed_model.summary()


# Remember that `None` is used to indicate that any integer may be expected. So, we use `None` to indicate batches of any size are acceptable. 
# 
# While model subclassing offers flexibility, it comes at a cost of greater complexity and more opportunities for
# user errors. So, we recommend, to always use the simplest tool for the job. 

# ### Your Turn to Build a Neural Network
# 
# <img src="assets/mlp_mnist.png" width=600px>
# 
# > **Exercise:** Use the subclassing method to create a network with 784 input units, a hidden layer with 128 units and a ReLU activation, then a hidden layer with 64 units and a ReLU activation, and finally an output layer with 10 units and a softmax activation function. You can use a ReLU activation function by setting `activation = 'relu'`. After you create your model, create a model object and build it.

# In[23]:


## Solution

class My_Network(tf.keras.Model):
    def __init__(self, num_classes = 10):
        super().__init__()
        self.num_classes = num_classes
    
        self.input_layer = tf.keras.layers.Flatten()
        self.hidden_1 = tf.keras.layers.Dense(128, activation = 'relu')
        self.hidden_2 = tf.keras.layers.Dense(64, activation = 'relu')
        self.output_layer = tf.keras.layers.Dense(self.num_classes, activation = 'softmax')
    
    def call(self, input_tensor):
        x = self.input_layer(input_tensor)
        x = self.hidden_1(x)
        x = self.hidden_2(x)
        x = self.output_layer(x)
    
        return x

my_model_2 = My_Network()

my_model_2.build((None, 28, 28, 1))

my_model_2.summary()


# ## Looking at Weights and Biases of Subclassed Models
# 
# As before, we can get the weights an biases of each layer in our subclassed models. In this case, we can use the name we gave to each layer in the `__init__` method to get the weights and biases of a particular layer. For example, in the exercise we gave the first hidden layer the name `hidden_1`, so we can get the weights an biases from this layer by using:

# In[24]:


w1 = my_model_2.hidden_1.get_weights()[0]
b1 = my_model_2.hidden_1.get_weights()[1]

print('\n\u2022 Weights:\n', w)
print('\n\u2022 Biases:\n', b)
print('\nThis layer has a total of {:,} weights and {:,} biases'.format(w1.size, b1.size))


# All the other methods we saw before, such as `.layers`, are also available for subclassed models, so feel free to use them.

# ## Making Predictions with Subclassed Models
# 
# Predictions are made in exactly the same way as before. So let's pass an image to our subclassed model and see what we get:

# In[25]:


for image_batch, label_batch in training_batches.take(1):
    ps = subclassed_model.predict(image_batch)
    first_image = image_batch.numpy().squeeze()[0]

fig, (ax1, ax2) = plt.subplots(figsize=(6,9), ncols=2)
ax1.imshow(first_image, cmap = plt.cm.binary)
ax1.axis('off')
ax2.barh(np.arange(10), ps[0])
ax2.set_aspect(0.1)
ax2.set_yticks(np.arange(10))
ax2.set_yticklabels(np.arange(10))
ax2.set_title('Class Probability')
ax2.set_xlim(0, 1.1)
plt.tight_layout()


# As before, we can see above, our model gives every digit roughly the same probability. This means our network has basically no idea what the digit in the image is. This is because we haven't trained our model yet, so all the weights are random!
# 
# In the next notebook, we'll see how we can train a neural network to accurately predict the numbers appearing in the MNIST images.

# ## Other Methods to Create Models

# In[26]:


model = tf.keras.Sequential()

model.add(tf.keras.layers.Flatten(input_shape = (28,28,1)))
model.add(tf.keras.layers.Dense(32, activation='relu'))
model.add(tf.keras.layers.Dense(10, activation='softmax'))
          
model.summary()


# In[27]:


layer_neurons = [512, 256, 128, 56, 28, 14]

model = tf.keras.Sequential()
model.add(tf.keras.layers.Flatten(input_shape = (28,28,1)))

for neurons in layer_neurons:
    model.add(tf.keras.layers.Dense(neurons, activation='relu'))
            
model.add(tf.keras.layers.Dense(10, activation='softmax'))
          
model.summary()        


# ## Clearing the Graph
# 
# In order to avoid clutter from old models in the graph, we can use:
# 
# ```python
# tf.keras.backend.clear_session()
# ```
# 
# This command deletes the current `tf.keras` graph and creates a new one.

# In[28]:


tf.keras.backend.clear_session()

layer_neurons = [512, 256, 128, 56, 28, 14]

model = tf.keras.Sequential()
model.add(tf.keras.layers.Flatten(input_shape = (28,28,1)))

for neurons in layer_neurons:
    model.add(tf.keras.layers.Dense(neurons, activation='relu'))
            
model.add(tf.keras.layers.Dense(10, activation='softmax'))
          
model.summary()    


# In[ ]:




