# automatically generated by the FlatBuffers compiler, do not modify

# namespace: NeuralaRecognizer

import flatbuffers
from flatbuffers.compat import import_numpy
np = import_numpy()

class HifiResults(object):
    __slots__ = ['_tab']

    @classmethod
    def GetRootAsHifiResults(cls, buf, offset):
        n = flatbuffers.encode.Get(flatbuffers.packer.uoffset, buf, offset)
        x = HifiResults()
        x.Init(buf, n + offset)
        return x

    # HifiResults
    def Init(self, buf, pos):
        self._tab = flatbuffers.table.Table(buf, pos)

    # HifiResults
    def Width(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(4))
        if o != 0:
            return self._tab.Get(flatbuffers.number_types.Uint32Flags, o + self._tab.Pos)
        return 0

    # HifiResults
    def Height(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(6))
        if o != 0:
            return self._tab.Get(flatbuffers.number_types.Uint32Flags, o + self._tab.Pos)
        return 0

    # HifiResults
    def AnomalyScore(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(8))
        if o != 0:
            return self._tab.Get(flatbuffers.number_types.Float32Flags, o + self._tab.Pos)
        return 0.0

    # HifiResults
    def Heatmap(self, j):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(10))
        if o != 0:
            a = self._tab.Vector(o)
            return self._tab.Get(flatbuffers.number_types.Float32Flags, a + flatbuffers.number_types.UOffsetTFlags.py_type(j * 4))
        return 0

    # HifiResults
    def HeatmapAsNumpy(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(10))
        if o != 0:
            return self._tab.GetVectorAsNumpy(flatbuffers.number_types.Float32Flags, o)
        return 0

    # HifiResults
    def HeatmapLength(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(10))
        if o != 0:
            return self._tab.VectorLen(o)
        return 0

    # HifiResults
    def HeatmapIsNone(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(10))
        return o == 0

def HifiResultsStart(builder): builder.StartObject(4)
def HifiResultsAddWidth(builder, width): builder.PrependUint32Slot(0, width, 0)
def HifiResultsAddHeight(builder, height): builder.PrependUint32Slot(1, height, 0)
def HifiResultsAddAnomalyScore(builder, anomalyScore): builder.PrependFloat32Slot(2, anomalyScore, 0.0)
def HifiResultsAddHeatmap(builder, heatmap): builder.PrependUOffsetTRelativeSlot(3, flatbuffers.number_types.UOffsetTFlags.py_type(heatmap), 0)
def HifiResultsStartHeatmapVector(builder, numElems): return builder.StartVector(4, numElems, 4)
def HifiResultsEnd(builder): return builder.EndObject()
