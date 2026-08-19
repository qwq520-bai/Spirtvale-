# Spirtvale-

旋风狂战自动刷红哥布林脚本。

## 当前内容

- `src/`：主程序源码、键鼠/目标辅助模块和训练入口。
- `models/spirt_three.pt`：当前最终 YOLO 模型（17 类）。
- `build/`：精简版 PyInstaller 配置和 Torch hook。

训练数据集、虚拟环境、缓存、runs 和打包成品未上传。继续训练时，需要另行准备 `training_data/merged_dataset_v3`。

运行主程序前安装项目依赖，并确保 SpiritVale 与 ViGEmBus 驱动已准备好。
