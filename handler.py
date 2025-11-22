"""
RunPod Serverless Handler 示例

这个文件演示如何使用打包在镜像中的模型来处理请求。
根据你的实际需求修改 handler 函数。
"""
import os
import runpod

# 设置模型缓存路径（模型已在镜像的 /models 目录中）
os.environ['MODELSCOPE_CACHE'] = '/models'
os.environ['TRANSFORMERS_CACHE'] = '/models'
os.environ['HF_HOME'] = '/models'

print("🔄 开始加载模型...")

# 在容器启动时加载模型（只加载一次，后续请求复用）
from modelscope.pipelines import pipeline

# 示例：加载说话人分割相关的模型
# 根据你的 projects/ 配置修改这里
try:
    vad_pipeline = pipeline(
        task='voice-activity-detection',
        model='damo/speech_fsmn_vad_zh-cn-16k-common-pytorch'
    )
    print("✅ VAD 模型加载完成")
    
    speaker_pipeline = pipeline(
        task='speaker-diarization',
        model='iic/speech_campplus_speaker-diarization_common'
    )
    print("✅ 说话人分割模型加载完成")
    
except Exception as e:
    print(f"❌ 模型加载失败: {e}")
    raise


def handler(event):
    """
    处理 RunPod Serverless 请求
    
    输入格式：
    {
        "input": {
            "task": "vad" 或 "speaker_diarization",
            "audio_url": "音频文件URL或路径",
            "params": {}  # 可选的额外参数
        }
    }
    
    返回格式：
    {
        "output": {
            "result": ...,
            "task": "..."
        }
    }
    或
    {
        "error": "错误信息"
    }
    """
    try:
        # 获取输入参数
        input_data = event.get("input", {})
        
        task_type = input_data.get("task", "vad")
        audio_input = input_data.get("audio_url") or input_data.get("audio")
        params = input_data.get("params", {})
        
        if not audio_input:
            return {"error": "缺少 audio_url 或 audio 参数"}
        
        print(f"📝 处理请求: task={task_type}, audio={audio_input[:50]}...")
        
        # 根据任务类型选择对应的模型
        if task_type == "vad":
            result = vad_pipeline(audio_input, **params)
            
        elif task_type == "speaker_diarization":
            result = speaker_pipeline(audio_input, **params)
            
        else:
            return {"error": f"不支持的任务类型: {task_type}"}
        
        print(f"✅ 处理完成")
        
        return {
            "output": {
                "task": task_type,
                "result": result
            }
        }
    
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        return {"error": str(e)}


# RunPod Serverless 启动入口
if __name__ == "__main__":
    print("🚀 RunPod Serverless Handler 已启动")
    print("📦 模型缓存目录:", os.environ.get('MODELSCOPE_CACHE'))
    
    runpod.serverless.start({"handler": handler})
