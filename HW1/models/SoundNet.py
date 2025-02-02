import numpy as np
import torch
import torch.nn as nn
from torch import bmm, cat, randn, zeros
from torch.autograd import Variable
import os

LEN_WAVEFORM = 22050 * 20

local_config = {
	'batch_size': 1,
	'eps': 1e-5,
	'sample_rate': 22050,
	'load_size': 22050 * 20,
	'name_scope': 'SoundNet_TF',
	'phase': 'extract',
}


class SoundNet(nn.Module):
	def __init__(self):
		super(SoundNet, self).__init__()
		
		self.conv1 = nn.Conv2d(1, 16, kernel_size=(64, 1), stride=(2, 1), padding=(32, 0))
		print("Conv1", self.conv1.weight.shape, self.conv1.bias.shape)
		self.batchnorm1 = nn.BatchNorm2d(16, eps=1e-5, momentum=0.1)
		print("Bn1", self.batchnorm1.weight.shape, self.batchnorm1.bias.shape)
		self.relu1 = nn.ReLU(True)
		self.maxpool1 = nn.MaxPool2d((8, 1), stride=(8, 1))

		self.conv2 = nn.Conv2d(16, 32, kernel_size=(32, 1), stride=(2, 1), padding=(16, 0))
		print("Conv2", self.conv2.weight.shape, self.conv2.bias.shape)
		self.batchnorm2 = nn.BatchNorm2d(32, eps=1e-5, momentum=0.1)
		print("Bn2", self.batchnorm2.weight.shape, self.batchnorm2.bias.shape)
		self.relu2 = nn.ReLU(True)
		self.maxpool2 = nn.MaxPool2d((8, 1), stride=(8, 1))

		self.conv3 = nn.Conv2d(32, 64, kernel_size=(16, 1), stride=(2, 1), padding=(8, 0))
		print("Conv3", self.conv3.weight.shape, self.conv3.bias.shape)
		self.batchnorm3 = nn.BatchNorm2d(64, eps=1e-5, momentum=0.1)
		print("Bn3", self.batchnorm3.weight.shape, self.batchnorm3.bias.shape)
		self.relu3 = nn.ReLU(True)

		# complete the layer4-6 blocks according to the params provided in the paper (https://arxiv.org/pdf/1610.09001.pdf) 

		self.conv4 = nn.Conv2d(64, 128, kernel_size=(8, 1), stride=(2, 1), padding=(4, 0))
		print("Conv4", self.conv4.weight.shape, self.conv4.bias.shape)
		self.batchnorm4 = nn.BatchNorm2d(128, eps=1e-5, momentum=0.1)
		print("Bn4", self.batchnorm4.weight.shape, self.batchnorm4.bias.shape)
		self.relu4 = nn.ReLU(True)

		self.conv5 = nn.Conv2d(128, 256, kernel_size=(4, 1), stride=(2, 1), padding=(2, 0))
		print("Conv5", self.conv5.weight.shape, self.conv5.bias.shape)
		self.batchnorm5 = nn.BatchNorm2d(256, eps=1e-5, momentum=0.1)
		print("Bn5", self.batchnorm5.weight.shape, self.batchnorm5.bias.shape)
		self.relu5 = nn.ReLU(True)
		self.maxpool5 = nn.MaxPool2d((4, 1), stride=(4, 1))

		self.conv6 = nn.Conv2d(256, 512, kernel_size=(4, 1), stride=(2, 1), padding=(2, 0))
		print("Conv6", self.conv6.weight.shape, self.conv6.bias.shape)
		self.batchnorm6 = nn.BatchNorm2d(512, eps=1e-5, momentum=0.1)
		print("Bn6", self.batchnorm6.weight.shape, self.batchnorm6.bias.shape)
		self.relu6 = nn.ReLU(True)


		# raise NotImplementedError("fill in the layer4-6 blocks first")

		self.conv7 = nn.Conv2d(512, 1024, kernel_size=(4, 1), stride=(2, 1), padding=(2, 0))
		print("Conv7", self.conv7.weight.shape, self.conv7.bias.shape)
		self.batchnorm7 = nn.BatchNorm2d(1024, eps=1e-5, momentum=0.1)
		print("Bn7", self.batchnorm7.weight.shape, self.batchnorm7.bias.shape)
		self.relu7 = nn.ReLU(True)

		self.conv8_objs = nn.Conv2d(1024, 1000, kernel_size=(8, 1), stride=(2, 1))
		print("Conv81", self.conv8_objs.weight.shape, self.conv8_objs.bias.shape)
		self.conv8_scns = nn.Conv2d(1024, 401, kernel_size=(8, 1), stride=(2, 1))
		print("Conv82", self.conv8_scns.weight.shape, self.conv8_scns.bias.shape)

	def forward(self, waveform):
		"""
			Args:
				waveform (Variable): Raw 20s waveform.
		"""
		if torch.cuda.is_available():
			waveform.cuda()

		output = dict()
		
		x = self.conv1(waveform)
		x = self.batchnorm1(x)
		x = self.relu1(x)
		x = self.maxpool1(x)

		x = self.conv2(x)
		x = self.batchnorm2(x)
		x = self.relu2(x)
		x = self.maxpool2(x)
		
		x = self.conv3(x)
		x = self.batchnorm3(x)
		x = self.relu3(x)

		#complete the processing steps of layer4-6

		x = self.conv4(x)
		x = self.batchnorm4(x)
		x = self.relu4(x)

		x = self.conv5(x)
		output['conv5'] = x.data
		x = self.batchnorm5(x)
		x = self.relu5(x)
		x = self.maxpool5(x)
		output['pool5'] = x.data

		x = self.conv6(x)
		output['conv6'] = x.data
		x = self.batchnorm6(x)
		x = self.relu6(x)

		# raise NotImplementedError("fill in the blank first")

		x = self.conv7(x)
		output['conv7'] = x.data
		x = self.batchnorm7(x)
		x = self.relu7(x)

		x_obj = self.conv8_objs(x)
		output['y_obj'] = x_obj.data

		x_scns = self.conv8_scns(x)
		output['y_scns'] = x_scns.data
		
		return output
	
	@staticmethod
	def load_param(batchnorm, conv, params_w, batch_norm=True):
		if batch_norm:
			bn_bs = params_w['beta']
			batchnorm.bias.data = torch.from_numpy(bn_bs)
			bn_ws = params_w['gamma']
			batchnorm.weight.data = torch.from_numpy(bn_ws)
			bn_mean = params_w['mean']
			batchnorm.running_mean.data = torch.from_numpy(bn_mean)
			bn_var = params_w['var']
			batchnorm.running_var.data = torch.from_numpy(bn_var)
		
		conv_bs = params_w['biases']
		conv.bias.data = torch.from_numpy(conv_bs)
		conv_ws = params_w['weights']
		conv.weight.data = torch.from_numpy(conv_ws).permute(3, 2, 0, 1)
		return batchnorm, conv
	
	def load_weights(self, model_path):
		param_G = np.load(model_path, encoding='latin1', allow_pickle=True).item()
		
		params_w = param_G['conv1']
		self.batchnorm1, self.conv1 = self.load_param(self.batchnorm1, self.conv1, params_w)
		
		params_w = param_G['conv2']
		self.batchnorm2, self.conv2 = self.load_param(self.batchnorm2, self.conv2, params_w)
		
		params_w = param_G['conv3']
		self.batchnorm3, self.conv3 = self.load_param(self.batchnorm3, self.conv3, params_w)
		
		#complete the weights loading for layer4-6

		params_w = param_G['conv4']
		self.batchnorm4, self.conv4 = self.load_param(self.batchnorm4, self.conv4, params_w)

		params_w = param_G['conv5']
		self.batchnorm5, self.conv5 = self.load_param(self.batchnorm5, self.conv5, params_w)

		params_w = param_G['conv6']
		self.batchnorm6, self.conv6 = self.load_param(self.batchnorm6, self.conv6, params_w)

		# raise NotImplementedError("finish the blank first")
		
		params_w = param_G['conv7']
		self.batchnorm7, self.conv7 = self.load_param(self.batchnorm7, self.conv7, params_w)
		
		params_w = param_G['conv8']
		_, self.conv8_objs = self.load_param([], self.conv8_objs, params_w, batch_norm=False)
		params_w = param_G['conv8_2']
		_, self.conv8_scns = self.load_param([], self.conv8_scns, params_w, batch_norm=False)