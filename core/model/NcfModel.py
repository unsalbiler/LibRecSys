import tensorflow as tf
from core.model.BaseModels import BaseRec
from keras.layers import Input, Multiply, concatenate, Dense, Input
from keras.constraints import NonNeg
from overrides import overrides
from core.utils import layers

class NcfModel():
    def __init__(self, user_count: int, item_count: int, gmf_dim: int, mlp_dim: int):
        self.mlp_model = MlpModel(user_count, item_count, mlp_dim, [64, 32, 16], "relu")
        self.gmf_model = GmfModel(user_count, item_count, gmf_dim)
        self.user_input = None 
        self.item_input = None
        self.merge_layer = None
        
        
    def _buildMergeLayer(self):
        self.merge_layer = concatenate([self.mlp_model.output_layer, self.gmf_model.merge_layer], axis = 1)
        return self.merge_layer
    
    
    def _buildNeuMfLayer(self):
        return Dense(units = 1, activation = "sigmoid", kernel_initializer = "lecun_uniform")(self.merge_layer)
    
    
    def _buildModelGraph(self):
        self.user_input = Input(shape = [1], dtype = tf.int32)
        self.item_input = Input(shape = [1], dtype = tf.int32)        
        
        self.gmf_model.user_input = self.user_input
        self.gmf_model.item_input = self.item_input
        
        self.mlp_model.user_input = self.user_input
        self.mlp_model.item_input = self.item_input
        
        self.mlp_model._buildGraph()
        self.gmf_model._buildGraph()
        
        self._buildMergeLayer()
        return self._buildNeuMfLayer()
    
    
class MlpModel(BaseRec):
    def __init__(self, user_count: int, item_count: int, latent_dim: int, unit_counts: list[int], activation: str):
        super().__init__(user_count, item_count, latent_dim)
        
        self.unit_counts = unit_counts
        self.activation = activation
        self.output_layer = None
        
    @overrides
    def _buildMergeLayer(self):
        self.merge_layer = concatenate([self.user_embedding_layer, self.item_embedding_layer], axis = 1)
        return self.merge_layer

    def _buildMlp(self, input_layer):
        return layers.denseSequenceFromList(input_layer, unit_counts = self.unit_counts, activation = self.activation)
    
    def _buildGraph(self):        
        self.user_embedding_layer = self._buildEmbedding(self.user_input, nonNeg = False)
        self.item_embedding_layer = self._buildEmbedding(self.item_input, nonNeg = False)
        
        self._buildMergeLayer()
        self.output_layer = self._buildMlp(self.merge_layer)
        
        return self.output_layer
    
    
class GmfModel(BaseRec):
    def __init__(self, user_count: int, item_count: int, latent_dim: int):
        super().__init__(user_count, item_count, latent_dim)
        
    @overrides
    def _buildMergeLayer(self):
        self.merge_layer = Multiply()([self.user_embedding, self.item_embedding])
        return self.merge_layer
    
    
    def _buildGraph(self):        
        self.user_embedding = self._buildEmbedding(self.user_input, nonNeg = True)
        self.item_embedding = self._buildEmbedding(self.item_input, nonNeg = True)
        
        return self._buildMergeLayer()
        