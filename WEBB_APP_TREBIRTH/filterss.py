
import pandas as pd
import numpy as np



coefLPF1HZ = [0.0023, 0.0015, 0.0019, 0.0025, 0.0031, 0.0037, 0.0045, 0.0053, 0.0062, 0.0071, 0.0082, 0.0093, 0.0104, 0.0115, 0.0127, 0.0139, 0.0152, 0.0164, 0.0176, 0.0187, 0.0198, 0.0208, 0.0218, 0.0226, 0.0234, 0.0241, 0.0246, 0.025, 0.0253, 0.0254, 0.0254, 0.0253, 0.025, 0.0246, 0.0241, 0.0234, 0.0226, 0.0218, 0.0208, 0.0198, 0.0187, 0.0176, 0.0164, 0.0152, 0.0139, 0.0127, 0.0115, 0.0104, 0.0093, 0.0082, 0.0071, 0.0062, 0.0053, 0.0045, 0.0037, 0.0031, 0.0025, 0.0019, 0.0015, 0.0023]
coefLPF2HZ = [0.0011, 0.0005, 0.0005, 0.0002, -0.0004, -0.0013, -0.0026, -0.0043, -0.0062, -0.0083, -0.0105, -0.0126, -0.0142, -0.0153, -0.0153, -0.0142, -0.0117, -0.0077, -0.002, 0.0052, 0.0138, 0.0236, 0.0342, 0.0451, 0.0558, 0.0658, 0.0745, 0.0816, 0.0865, 0.089, 0.089, 0.0865, 0.0816, 0.0745, 0.0658, 0.0558, 0.0451, 0.0342, 0.0236, 0.0138, 0.0052, -0.002, -0.0077, -0.0117, -0.0142, -0.0153, -0.0153, -0.0142, -0.0126, -0.0105, -0.0083, -0.0062, -0.0043, -0.0026, -0.0013, -0.0004, 0.0002, 0.0005, 0.0005, 0.0011]
coefLPF3HZ = [0.0003, -0.0011, -0.0023, -0.0041, -0.0064, -0.0086, -0.0102, -0.0106, -0.0093, -0.0062, -0.0014, 0.0044, 0.0099, 0.0139, 0.0151, 0.0125, 0.0061, -0.0035, -0.0144, -0.0242, -0.0301, -0.0294, -0.0203, -0.0021, 0.024, 0.0556, 0.0887, 0.119, 0.1421, 0.1546, 0.1546, 0.1421, 0.119, 0.0887, 0.0556, 0.024, -0.0021, -0.0203, -0.0294, -0.0301, -0.0242, -0.0144, -0.0035, 0.0061, 0.0125, 0.0151, 0.0139, 0.0099, 0.0044, -0.0014, -0.0062, -0.0093, -0.0106, -0.0102, -0.0086, -0.0064, -0.0041, -0.0023, -0.0011, 0.0003]
coefLPF4HZ = [-0.0007, -0.0033, -0.0057, -0.0087, -0.0104, -0.0097, -0.0061, -0.0003, 0.0059, 0.0099, 0.0095, 0.0042, -0.0042, -0.0122, -0.0154, -0.0113, -0.0004, 0.0134, 0.0233, 0.0234, 0.0109, -0.0112, -0.0341, -0.0461, -0.0365, -0.0008, 0.057, 0.1243, 0.1837, 0.2185, 0.2185, 0.1837, 0.1243, 0.057, -0.0008, -0.0365, -0.0461, -0.0341, -0.0112, 0.0109, 0.0234, 0.0233, 0.0134, -0.0004, -0.0113, -0.0154, -0.0122, -0.0042, 0.0042, 0.0095, 0.0099, 0.0059, -0.0003, -0.0061, -0.0097, -0.0104, -0.0087, -0.0057, -0.0033, -0.0007]
coefLPF5HZ = [-0.0022, -0.0058, -0.0094, -0.0113, -0.0088, -0.0024, 0.0051, 0.0087, 0.0059, -0.0022, -0.0097, -0.0105, -0.0025, 0.0092, 0.0156, 0.01, -0.0054, -0.0198, -0.0205, -0.0034, 0.0213, 0.0342, 0.0206, -0.0167, -0.0535, -0.0565, -0.0041, 0.0962, 0.2072, 0.2799, 0.2799, 0.2072, 0.0962, -0.0041, -0.0565, -0.0535, -0.0167, 0.0206, 0.0342, 0.0213, -0.0034, -0.0205, -0.0198, -0.0054, 0.01, 0.0156, 0.0092, -0.0025, -0.0105, -0.0097, -0.0022, 0.0059, 0.0087, 0.0051, -0.0024, -0.0088, -0.0113, -0.0094, -0.0058, -0.0022]
coefLPF6HZ = [-0.0028, -0.0067, -0.0088, -0.0055, 0.0031, 0.0114, 0.012, 0.0041, -0.0048, -0.005, 0.0047, 0.0137, 0.0107, -0.0035, -0.0139, -0.0069, 0.0123, 0.0223, 0.0083, -0.0184, -0.0273, -0.0023, 0.0349, 0.0399, -0.0062, -0.0648, -0.0623, 0.0429, 0.211, 0.3387, 0.3387, 0.211, 0.0429, -0.0623, -0.0648, -0.0062, 0.0399, 0.0349, -0.0023, -0.0273, -0.0184, 0.0083, 0.0223, 0.0123, -0.0069, -0.0139, -0.0035, 0.0107, 0.0137, 0.0047, -0.005, -0.0048, 0.0041, 0.012, 0.0114, 0.0031, -0.0055, -0.0088, -0.0067, -0.0028]
coefLPF7HZ = [-0.0031, -0.0066, -0.005, 0.0042, 0.0142, 0.0139, 0.0029, -0.0053, 0.0001, 0.0107, 0.0089, -0.0052, -0.0113, 0.0018, 0.0159, 0.0073, -0.0149, -0.0164, 0.01, 0.0264, 0.0019, -0.0328, -0.0205, 0.033, 0.0479, -0.0205, -0.0895, -0.0229, 0.193, 0.3926, 0.3926, 0.193, -0.0229, -0.0895, -0.0205, 0.0479, 0.033, -0.0205, -0.0328, 0.0019, 0.0264, 0.01, -0.0164, -0.0149, 0.0073, 0.0159, 0.0018, -0.0113, -0.0052, 0.0089, 0.0107, 0.0001, -0.0053, 0.0029, 0.0139, 0.0142, 0.0042, -0.005, -0.0066, -0.0031]
coefLPF8HZ = [-0.0034, -0.0057, 0.0009, 0.0137, 0.0168, 0.0044, -0.0056, 0.0016, 0.0104, 0.0017, -0.0102, -0.0016, 0.0128, 0.0034, -0.015, -0.0051, 0.0181, 0.0078, -0.0218, -0.0115, 0.0268, 0.0169, -0.034, -0.0255, 0.0458, 0.0414, -0.0701, -0.082, 0.1566, 0.4428, 0.4428, 0.1566, -0.082, -0.0701, 0.0414, 0.0458, -0.0255, -0.034, 0.0169, 0.0268, -0.0115, -0.0218, 0.0078, 0.0181, -0.0051, -0.015, 0.0034, 0.0128, -0.0016, -0.0102, 0.0017, 0.0104, 0.0016, -0.0056, 0.0044, 0.0168, 0.0137, 0.0009, -0.0057, -0.0034]
coefLPF9HZ = [-0.0037, -0.004, 0.0079, 0.0192, 0.0102, -0.0051, -0.0003, 0.0095, -0.0009, -0.0092, 0.0053, 0.0092, -0.0096, -0.0074, 0.0146, 0.0035, -0.0191, 0.0031, 0.0226, -0.0128, -0.0236, 0.0259, 0.0206, -0.0435, -0.0106, 0.0691, -0.0146, -0.1191, 0.105, 0.4882, 0.4882, 0.105, -0.1191, -0.0146, 0.0691, -0.0106, -0.0435, 0.0206, 0.0259, -0.0236, -0.0128, 0.0226, 0.0031, -0.0191, 0.0035, 0.0146, -0.0074, -0.0096, 0.0092, 0.0053, -0.0092, -0.0009, 0.0095, -0.0003, -0.0051, 0.0102, 0.0192, 0.0079, -0.004, -0.0037]
coefLPF10HZ = [-0.0042, -0.0018, 0.0145, 0.019, 0.0003, -0.0044, 0.0084, 0.0007, -0.0084, 0.0068, 0.0047, -0.0117, 0.0041, 0.0108, -0.0138, -0.0017, 0.0184, -0.0132, -0.0117, 0.0265, -0.0076, -0.0277, 0.034, 0.0074, -0.0545, 0.0398, 0.0484, -0.1243, 0.043, 0.5282, 0.5282, 0.043, -0.1243, 0.0484, 0.0398, -0.0545, 0.0074, 0.034, -0.0277, -0.0076, 0.0265, -0.0117, -0.0132, 0.0184, -0.0017, -0.0138, 0.0108, 0.0041, -0.0117, 0.0047, 0.0068, -0.0084, 0.0007, 0.0084, -0.0044, 0.0003, 0.019, 0.0145, -0.0018, -0.0042]
coefLPF11HZ = [-0.0053, -0.0001, 0.0194, 0.0141, -0.0053, 0.0041, 0.0055, -0.0083, 0.005, 0.004, -0.0105, 0.0082, 0.0026, -0.0131, 0.013, -0.0001, -0.0158, 0.0198, -0.0051, -0.0185, 0.0298, -0.0143, -0.0207, 0.0466, -0.0336, -0.0224, 0.0865, -0.0961, -0.0232, 0.5624, 0.5624, -0.0232, -0.0961, 0.0865, -0.0224, -0.0336, 0.0466, -0.0207, -0.0143, 0.0298, -0.0185, -0.0051, 0.0198, -0.0158, -0.0001, 0.013, -0.0131, 0.0026, 0.0082, -0.0105, 0.004, 0.005, -0.0083, 0.0055, 0.0041, -0.0053, 0.0141, 0.0194, -0.0001, -0.0053]
coefLPF12HZ = [-0.0088, -0.0026, 0.0203, 0.0084, -0.0015, 0.0106, -0.0035, 0.0008, 0.0072, -0.0094, 0.008, -0.0003, -0.0085, 0.0142, -0.0119, 0.0018, 0.0118, -0.0211, 0.0193, -0.0047, -0.0168, 0.0337, -0.0339, 0.0118, 0.0272, -0.0661, 0.0801, -0.0421, -0.0872, 0.5906, 0.5906, -0.0872, -0.0421, 0.0801, -0.0661, 0.0272, 0.0118, -0.0339, 0.0337, -0.0168, -0.0047, 0.0193, -0.0211, 0.0118, 0.0018, -0.0119, 0.0142, -0.0085, -0.0003, 0.008, -0.0094, 0.0072, 0.0008, -0.0035, 0.0106, -0.0015, 0.0084, 0.0203, -0.0026, -0.0088]
coefLPF13HZ = [-0.017, -0.0148, 0.0091, -0.0046, 0.0004, 0.0036, -0.0068, 0.0083, -0.0074, 0.004, 0.0015, -0.0076, 0.0123, -0.0138, 0.0108, -0.0035, -0.0066, 0.0169, -0.0237, 0.024, -0.0161, 0.0001, 0.0209, -0.0418, 0.0557, -0.0552, 0.0324, 0.0232, -0.1426, 0.6122, 0.6122, -0.1426, 0.0232, 0.0324, -0.0552, 0.0557, -0.0418, 0.0209, 0.0001, -0.0161, 0.024, -0.0237, 0.0169, -0.0066, -0.0035, 0.0108, -0.0138, 0.0123, -0.0076, 0.0015, 0.004, -0.0074, 0.0083, -0.0068, 0.0036, 0.0004, -0.0046, 0.0091, -0.0148, -0.017]
coefLPF14HZ = [-0.0216, -0.0117, 0.0096, -0.0081, 0.0066, -0.0049, 0.0027, 0.0, -0.0031, 0.0064, -0.0094, 0.0116, -0.0127, 0.0122, -0.0099, 0.0056, 0.0004, -0.0077, 0.0157, -0.0235, 0.0299, -0.0339, 0.0342, -0.0295, 0.0184, 0.0008, -0.0315, 0.082, -0.1838, 0.6269, 0.6269, -0.1838, 0.082, -0.0315, 0.0008, 0.0184, -0.0295, 0.0342, -0.0339, 0.0299, -0.0235, 0.0157, -0.0077, 0.0004, 0.0056, -0.0099, 0.0122, -0.0127, 0.0116, -0.0094, 0.0064, -0.0031, 0.0, 0.0027, -0.0049, 0.0066, -0.0081, 0.0096, -0.0117, -0.0216]
coefLPF15HZ = [-0.0004, 0.0004, -0.0006, 0.0008, -0.0011, 0.0014, -0.0018, 0.0023, -0.0029, 0.0036, -0.0044, 0.0054, -0.0065, 0.0078, -0.0093, 0.0111, -0.0131, 0.0154, -0.0181, 0.0213, -0.0252, 0.0298, -0.0356, 0.0429, -0.0527, 0.0664, -0.0875, 0.1249, -0.2107, 0.6361, 0.6361, -0.2107, 0.1249, -0.0875, 0.0664, -0.0527, 0.0429, -0.0356, 0.0298, -0.0252, 0.0213, -0.0181, 0.0154, -0.0131, 0.0111, -0.0093, 0.0078, -0.0065, 0.0054, -0.0044, 0.0036, -0.0029, 0.0023, -0.0018, 0.0014, -0.0011, 0.0008, -0.0006, 0.0004, -0.0004]
coefHPF1HZ = [-0.0017, -0.0012, -0.0016, -0.0021, -0.0026, -0.0033, -0.004, -0.0048, -0.0056, -0.0066, -0.0076, -0.0088, -0.0099, -0.0112, -0.0125, -0.0138, -0.0152, -0.0166, -0.018, -0.0194, -0.0207, -0.0221, -0.0234, -0.0246, -0.0257, -0.0267, -0.0276, -0.0285, -0.0291, -0.0297, -0.03, -0.0303, 0.9697, -0.0303, -0.03, -0.0297, -0.0291, -0.0285, -0.0276, -0.0267, -0.0257, -0.0246, -0.0234, -0.0221, -0.0207, -0.0194, -0.018, -0.0166, -0.0152, -0.0138, -0.0125, -0.0112, -0.0099, -0.0088, -0.0076, -0.0066, -0.0056, -0.0048, -0.004, -0.0033, -0.0026, -0.0021, -0.0016, -0.0012, -0.0017]
coefHPF2HZ = [-0.0145, 0.0138, 0.0086, 0.0051, 0.0024, 0.0, -0.0023, -0.0045, -0.0064, -0.0078, -0.0084, -0.0079, -0.0063, -0.0035, 0.0005, 0.0051, 0.0101, 0.0146, 0.0181, 0.0198, 0.0191, 0.0155, 0.0088, -0.0011, -0.0138, -0.0286, -0.0448, -0.0612, -0.0768, -0.0903, -0.1008, -0.1075, 0.8903, -0.1075, -0.1008, -0.0903, -0.0768, -0.0612, -0.0448, -0.0286, -0.0138, -0.0011, 0.0088, 0.0155, 0.0191, 0.0198, 0.0181, 0.0146, 0.0101, 0.0051, 0.0005, -0.0035, -0.0063, -0.0079, -0.0084, -0.0078, -0.0064, -0.0045, -0.0023, 0.0, 0.0024, 0.0051, 0.0086, 0.0138, -0.0145]
coefHPF3HZ = [-0.0126, 0.0126, 0.007, 0.0028, -0.0007, -0.0038, -0.0059, -0.0065, -0.0051, -0.0018, 0.0028, 0.0073, 0.0102, 0.0102, 0.0067, 0.0002, -0.0078, -0.0148, -0.0182, -0.0162, -0.0081, 0.0047, 0.0193, 0.0312, 0.0356, 0.0289, 0.0091, -0.0226, -0.0626, -0.1046, -0.1417, -0.1671, 0.8239, -0.1671, -0.1417, -0.1046, -0.0626, -0.0226, 0.0091, 0.0289, 0.0356, 0.0312, 0.0193, 0.0047, -0.0081, -0.0162, -0.0182, -0.0148, -0.0078, 0.0002, 0.0067, 0.0102, 0.0102, 0.0073, 0.0028, -0.0018, -0.0051, -0.0065, -0.0059, -0.0038, -0.0007, 0.0028, 0.007, 0.0126, -0.0126]
coefHPF4HZ = [-0.0028, -0.007, 0.0173, -0.0001, -0.0031, -0.0062, -0.0055, -0.0019, 0.0033, 0.0074, 0.0077, 0.0033, -0.004, -0.0103, -0.0115, -0.0057, 0.0049, 0.0147, 0.0175, 0.0098, -0.0058, -0.0217, -0.0278, -0.0179, 0.0066, 0.0348, 0.0505, 0.0386, -0.007, -0.0791, -0.1583, -0.2197, 0.7572, -0.2197, -0.1583, -0.0791, -0.007, 0.0386, 0.0505, 0.0348, 0.0066, -0.0179, -0.0278, -0.0217, -0.0058, 0.0098, 0.0175, 0.0147, 0.0049, -0.0057, -0.0115, -0.0103, -0.004, 0.0033, 0.0077, 0.0074, 0.0033, -0.0019, -0.0055, -0.0062, -0.0031, -0.0001, 0.0173, -0.007, -0.0028]
coefHPF5HZ = [0.0012, -0.0114, 0.0149, 0.0021, -0.006, -0.0065, -0.0015, 0.0047, 0.0073, 0.0034, -0.0043, -0.0093, -0.0062, 0.0036, 0.0119, 0.0103, -0.0017, -0.0146, -0.016, -0.0019, 0.0174, 0.0243, 0.0087, -0.0199, -0.037, -0.0217, 0.0219, 0.0612, 0.0533, -0.0232, -0.1475, -0.2628, 0.6903, -0.2628, -0.1475, -0.0232, 0.0533, 0.0612, 0.0219, -0.0217, -0.037, -0.0199, 0.0087, 0.0243, 0.0174, -0.0019, -0.016, -0.0146, -0.0017, 0.0103, 0.0119, 0.0036, -0.0062, -0.0093, -0.0043, 0.0034, 0.0073, 0.0047, -0.0015, -0.0065, -0.006, 0.0021, 0.0149, -0.0114, 0.0012]
coefHPF6HZ = [0.0023, -0.0114, 0.0138, 0.0003, -0.0073, -0.004, 0.0038, 0.0068, 0.0012, -0.0067, -0.0069, 0.0023, 0.0101, 0.0055, -0.0076, -0.013, -0.0014, 0.0146, 0.0139, -0.0064, -0.0225, -0.011, 0.0191, 0.0304, 0.0014, -0.0392, -0.037, 0.0224, 0.0782, 0.0415, -0.1111, -0.2943, 0.6236, -0.2943, -0.1111, 0.0415, 0.0782, 0.0224, -0.037, -0.0392, 0.0014, 0.0304, 0.0191, -0.011, -0.0225, -0.0064, 0.0139, 0.0146, -0.0014, -0.013, -0.0076, 0.0055, 0.0101, 0.0023, -0.0069, -0.0067, 0.0012, 0.0068, 0.0038, -0.004, -0.0073, 0.0003, 0.0138, -0.0114, 0.0023]
coefHPF7HZ = [0.0027, -0.0105, 0.0128, -0.002, -0.0072, 0.0002, 0.0066, 0.0021, -0.0065, -0.0048, 0.0057, 0.0079, -0.0039, -0.0109, 0.0005, 0.0134, 0.0045, -0.0147, -0.0111, 0.0137, 0.0191, -0.0096, -0.0278, 0.0012, 0.0367, 0.0135, -0.0448, -0.0387, 0.0513, 0.0903, -0.0555, -0.3129, 0.557, -0.3129, -0.0555, 0.0903, 0.0513, -0.0387, -0.0448, 0.0135, 0.0367, 0.0012, -0.0278, -0.0096, 0.0191, 0.0137, -0.0111, -0.0147, 0.0045, 0.0134, 0.0005, -0.0109, -0.0039, 0.0079, 0.0057, -0.0048, -0.0065, 0.0021, 0.0066, 0.0002, -0.0072, -0.002, 0.0128, -0.0105, 0.0027]
coefHPF8HZ = [0.0029, -0.0095, 0.0116, -0.004, -0.0058, 0.0041, 0.0049, -0.0046, -0.0052, 0.0057, 0.0056, -0.0072, -0.0062, 0.0091, 0.0067, -0.0116, -0.0073, 0.0147, 0.0078, -0.0186, -0.0082, 0.0238, 0.0086, -0.0311, -0.009, 0.0421, 0.0092, -0.0612, -0.0094, 0.1046, 0.0096, -0.3178, 0.4904, -0.3178, 0.0096, 0.1046, -0.0094, -0.0612, 0.0092, 0.0421, -0.009, -0.0311, 0.0086, 0.0238, -0.0082, -0.0186, 0.0078, 0.0147, -0.0073, -0.0116, 0.0067, 0.0091, -0.0062, -0.0072, 0.0056, 0.0057, -0.0052, -0.0046, 0.0049, 0.0041, -0.0058, -0.004, 0.0116, -0.0095, 0.0029]
coefHPF9HZ = [0.0028, -0.007, 0.0082, -0.0025, -0.0063, 0.0089, -0.0024, -0.0044, 0.0012, 0.0079, -0.0088, -0.0017, 0.0085, 0.0001, -0.0129, 0.009, 0.0086, -0.0136, -0.0052, 0.0213, -0.0067, -0.0213, 0.0184, 0.0188, -0.0356, -0.0039, 0.0498, -0.0218, -0.0647, 0.0798, 0.0724, -0.3082, 0.4231, -0.3082, 0.0724, 0.0798, -0.0647, -0.0218, 0.0498, -0.0039, -0.0356, 0.0188, 0.0184, -0.0213, -0.0067, 0.0213, -0.0052, -0.0136, 0.0086, 0.009, -0.0129, 0.0001, 0.0085, -0.0017, -0.0088, 0.0079, 0.0012, -0.0044, -0.0024, 0.0089, -0.0063, -0.0025, 0.0082, -0.007, 0.0028]
coefHPF10HZ = [0.0018, -0.0036, 0.0034, 0.0008, -0.0074, 0.0115, -0.0087, 0.0007, 0.0052, -0.003, -0.0053, 0.0101, -0.0045, -0.007, 0.0115, -0.0023, -0.0121, 0.0148, 0.0003, -0.0183, 0.0174, 0.006, -0.0278, 0.02, 0.0163, -0.043, 0.0219, 0.0387, -0.0762, 0.0232, 0.124, -0.2864, 0.357, -0.2864, 0.124, 0.0232, -0.0762, 0.0387, 0.0219, -0.043, 0.0163, 0.02, -0.0278, 0.006, 0.0174, -0.0183, 0.0003, 0.0148, -0.0121, -0.0023, 0.0115, -0.007, -0.0045, 0.0101, -0.0053, -0.003, 0.0052, 0.0007, -0.0087, 0.0115, -0.0074, 0.0008, 0.0034, -0.0036, 0.0018]
coefHPF11HZ = [0.0013, -0.0021, 0.0019, 0.0006, -0.0051, 0.0095, -0.0109, 0.0075, -0.0005, -0.0059, 0.0071, -0.0018, -0.0065, 0.0114, -0.0078, -0.0031, 0.0135, -0.0145, 0.0033, 0.0134, -0.0225, 0.0142, 0.0087, -0.0303, 0.0313, -0.0042, -0.037, 0.0612, -0.0379, -0.0415, 0.1534, -0.2514, 0.2903, -0.2514, 0.1534, -0.0415, -0.0379, 0.0612, -0.037, -0.0042, 0.0313, -0.0303, 0.0087, 0.0142, -0.0225, 0.0134, 0.0033, -0.0145, 0.0135, -0.0031, -0.0078, 0.0114, -0.0065, -0.0018, 0.0071, -0.0059, -0.0005, 0.0075, -0.0109, 0.0095, -0.0051, 0.0006, 0.0019, -0.0021, 0.0013]
coefHPF12HZ = [0.0011, -0.0014, 0.0014, -0.0002, -0.0023, 0.0056, -0.0088, 0.0103, -0.0089, 0.0045, 0.0017, -0.0073, 0.0097, -0.0073, 0.0003, 0.0084, -0.0146, 0.0146, -0.0069, -0.0061, 0.019, -0.025, 0.019, -0.001, -0.0229, 0.0421, -0.0447, 0.0223, 0.0255, -0.0903, 0.1563, -0.2054, 0.2235, -0.2054, 0.1563, -0.0903, 0.0255, 0.0223, -0.0447, 0.0421, -0.0229, -0.001, 0.019, -0.025, 0.019, -0.0061, -0.0069, 0.0146, -0.0146, 0.0084, 0.0003, -0.0073, 0.0097, -0.0073, 0.0017, 0.0045, -0.0089, 0.0103, -0.0088, 0.0056, -0.0023, -0.0002, 0.0014, -0.0014, 0.0011]
coefHPF13HZ = [0.001, -0.0011, 0.0013, -0.0011, 0.0002, 0.0014, -0.0036, 0.0062, -0.0086, 0.0102, -0.0103, 0.0086, -0.0048, -0.0004, 0.0063, -0.0115, 0.0146, -0.0143, 0.0101, -0.0021, -0.0085, 0.0193, -0.0278, 0.031, -0.0264, 0.0129, 0.0095, -0.0389, 0.072, -0.1046, 0.132, -0.1504, 0.1568, -0.1504, 0.132, -0.1046, 0.072, -0.0389, 0.0095, 0.0129, -0.0264, 0.031, -0.0278, 0.0193, -0.0085, -0.0021, 0.0101, -0.0143, 0.0146, -0.0115, 0.0063, -0.0004, -0.0048, 0.0086, -0.0103, 0.0102, -0.0086, 0.0062, -0.0036, 0.0014, 0.0002, -0.0011, 0.0013, -0.0011, 0.001]
coefHPF14HZ = [0.001, -0.001, 0.0014, -0.0017, 0.0018, -0.0018, 0.0015, -0.0008, -0.0002, 0.0017, -0.0037, 0.0059, -0.0083, 0.0108, -0.013, 0.0147, -0.0156, 0.0154, -0.0139, 0.0108, -0.0061, -0.0003, 0.0083, -0.0177, 0.0281, -0.0391, 0.0502, -0.0609, 0.0706, -0.0788, 0.0849, -0.0888, 0.0901, -0.0888, 0.0849, -0.0788, 0.0706, -0.0609, 0.0502, -0.0391, 0.0281, -0.0177, 0.0083, -0.0003, -0.0061, 0.0108, -0.0139, 0.0154, -0.0156, 0.0147, -0.013, 0.0108, -0.0083, 0.0059, -0.0037, 0.0017, -0.0002, -0.0008, 0.0015, -0.0018, 0.0018, -0.0017, 0.0014, -0.001, 0.001]
coefHPF15HZ = [0.0013, -0.001, 0.0013, -0.0017, 0.0022, -0.0028, 0.0034, -0.0041, 0.0049, -0.0057, 0.0066, -0.0076, 0.0087, -0.0098, 0.011, -0.0122, 0.0135, -0.0148, 0.016, -0.0173, 0.0186, -0.0198, 0.021, -0.0221, 0.0231, -0.0241, 0.025, -0.0257, 0.0263, -0.0268, 0.0272, -0.0274, 0.0275, -0.0274, 0.0272, -0.0268, 0.0263, -0.0257, 0.025, -0.0241, 0.0231, -0.0221, 0.021, -0.0198, 0.0186, -0.0173, 0.016, -0.0148, 0.0135, -0.0122, 0.011, -0.0098, 0.0087, -0.0076, 0.0066, -0.0057, 0.0049, -0.0041, 0.0034, -0.0028, 0.0022, -0.0017, 0.0013, -0.001, 0.0013]
