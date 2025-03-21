class Cargo(object):
    UP = 1
    RIGHT = 2

    def __init__(self, cargo_id, length=0, width=0, height=0, dict_input=None):
        """
        接收传入一个dict或者 长、宽、高数据
        :param cargo_id: 货物编号，用于唯一标识货物
        :param length:
        :param width:
        :param height:
        :param dict_input: {"Length": xx, "Width": xx, "Height": xx, "Quantity": xx}
        """
        assert any([all([length, width, height]), dict_input]), "Expect <dict>/<length, width, length> here"
        if isinstance(dict_input, dict):
            temp_list = [dict_input["Length"], dict_input["Width"], dict_input["Height"]]
        else:
            temp_list = [length, width, height]

        temp_list.sort(reverse=True)
        self.length, self.width, self.height = temp_list
        self.vol = self.length * self.width * self.height

        self.id = cargo_id
        self.location = None
        self.parent = None