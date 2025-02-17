import scipy.io as sio
import matplotlib.pyplot as plt

# 文件路径
mat_file_path = 'tmp/FallingMarble_res.mat'

# 读取 MAT 文件内容
mat_contents = sio.loadmat(mat_file_path)

# 检查 MAT 文件内容
print("MAT 文件内容 (顶级键):", mat_contents.keys())

# 假设 'data_2' 包含我们需要的数据，在进一步提取数据前确认它的结构
data_2_contents = mat_contents['data_2']
print("data_2 内容:", data_2_contents)

# 假设 data_2 是一个二维数组，其中包含时间、速度、高度和加速度
# 确保根据实际结构调整索引
time = data_2_contents[:, 0]          # 第一列是时间
height = data_2_contents[:, 1]        # 第二列是高度
velocity = data_2_contents[:, 2]      # 第三列是速度
acceleration = data_2_contents[:, 3]  # 第四列是加速度

# 绘制图表
plt.figure(figsize=(10, 6))
plt.subplot(3, 1, 1)
plt.plot(time, height, label='Height (m)')
plt.xlabel('Time (s)')
plt.ylabel('Height (m)')
plt.title('Height of Marble vs. Time')
plt.legend()
plt.grid(True)

plt.subplot(3, 1, 2)
plt.plot(time, velocity, label='Velocity (m/s)')
plt.xlabel('Time (s)')
plt.ylabel('Velocity (m/s)')
plt.title('Velocity of Marble vs. Time')
plt.legend()
plt.grid(True)

plt.subplot(3, 1, 3)
plt.plot(time, acceleration, label='Acceleration (m/s^2)')
plt.xlabel('Time (s)')
plt.ylabel('Acceleration (m/s^2)')
plt.title('Acceleration of Marble vs. Time')
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.show()
