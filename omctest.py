import OMPython

try:
    from OMPython import OMCSessionZMQ
    omc = OMCSessionZMQ()
    result = omc.sendExpression("getVersion()")
    print(f"OMC版本: {result}")
except Exception as e:
    print(f"启动OMPython时遇到问题: {e}")
