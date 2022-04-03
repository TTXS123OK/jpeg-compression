class APP0:
    segment_length = 0
    interchange_format = 0
    main_version_number = 0
    sub_version_number = 0
    density_unit = 0    # 0: 无单位; 1: 点数/英寸; 2: 点数/厘米
    X_density = 0
    Y_density = 0
    thumbnail_X = 0
    thumbnail_Y = 0
    thumbnail = []

    def __str__(self):
        print("segment_length: %d" % self.segment_length)
        print("interchange_format: %s" % self.interchange_format)
        print("main_version_number: %d" % self.main_version_number)
        print("sub_version_number: %d" % self.sub_version_number)
        print("density_unit: %d" % self.density_unit)
        print("X_density: %d" % self.X_density)
        print("Y_density: %d" % self.Y_density)
        print("thumbnail_X: %d" % self.thumbnail_X)
        print("thumbnail_Y: %d" % self.thumbnail_Y)
        return ''


class DQT:
    segment_length = 0
    QT_information = 0
    QT = [[], [], [], []]


class SOF0:
    segment_length = 0
    sample_precision = 0
    height = 0
    weight = 0
    component_num = 0
    components = {}


class DHT:
    segment_length = 0
    HT_information = 0  # 0－3位:HT号; 4位:HT类型, 0＝DC表，1＝AC表; 5－7位：必须＝0
    HT_bit = []
    HT_value_ac = [{}, {}, {}, {}]
    HT_value_dc = [{}, {}, {}, {}]


class SOS:
    segment_length = 0
    component_num = 0
    components = {}


class JPEG:
    APP0 = APP0()
    DQT = DQT()
    SOF0 = SOF0()
    DHT = DHT()
    SOS = SOS()

    def get_dc_table(self):
        return self.DHT.HT_value_dc

    def get_ac_table(self):
        return self.DHT.HT_value_ac
