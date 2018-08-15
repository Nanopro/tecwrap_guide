import tecplot as tp, tecplot
import numpy as np
import os
import subprocess
import psutil
from typing import List, Tuple
from collections import namedtuple

class TecWrapper:
    def __init__(self, cwd=None):
        self.cwd = cwd
        if self.cwd is None:
            self.cwd = os.getcwd()

        if 'tec360.exe' not in list(p.name() for p in psutil.process_iter()):
            if os.environ.get('TEC360_PATH'):
                self.proc = subprocess.Popen(
                    r'{path}/tec360.exe "{path}/startTecUtilServer.mcr"'.format(path = os.environ['TEC360_PATH']))
            else:
                raise EnvironmentError('Please, initialize TEC360_PATH env. variable with valid path to TecPlot360/bin directory.')
        try:
            tp.session.connect(timeout=30)
        except tp.exception.TecplotTimeoutError as error:
            raise SystemError("TecPlot is launched but is not reachable. Please make sure you are listening on port 7600.")

    def change_cwd(self, new_cwd):
        self.cwd = new_cwd

    def __call__(self, path_to_file):
        file = os.path.join(self.cwd, path_to_file)
        print(file)
        if path_to_file[-3:].lower() == 'dtf':
            print(os.system(r'dtf_to_tec.exe {input} {out} 1'.format(input=file, out=file[:-3] + 'tec')))
            file = file[:-3] + 'tec'
        self.session = TecSession(file)
        return self.session

    def close(self):
        try:
            self.proc.kill()
        except:
            print('Tec360 был запущен другим потоком')


class TecSession:
    def __init__(self, file_name):
        self.dataset = tp.data.load_tecplot(file_name, read_data_option=tp.constant.ReadDataOption.ReplaceInActiveFrame)
        self.frame = tp.active_frame()
        self.plot = self.frame.plot()
        try:
            self.dataset.variable('Z')
            self.model_type = '3D'
        except tp.exception.TecplotPatternMatchError:
            self.model_type = '2D'
            self.setup_fake_plane()
        self.base_zones = self.frame.active_zones()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        if exc_val:
            raise
    def show_contour(self, variable = 'X'):
        self.plot.show_contour = True
        self.plot.contour(0).variable = self.dataset.variable(variable)

    def execute_equation(self, equation):
        tp.data.operate.execute_equation(equation=equation)


    def setup_fake_plane(self):
        tp.data.operate.execute_equation(equation='{Z_NULL}=0')
        self.frame.plot_type = tp.constant.PlotType.Cartesian3D
        self.frame.plot().axes.z_axis.variable = self.dataset.variable('Z_NULL')

    def _get_slice(self, origin=(0, 0, 0), normal=(1, 0, 0), values=('Y', 'U'),
                   source=tp.constant.SliceSource.VolumeZones):
        '''

        :param tuple[float] origin: asdasd
        :param tuple[float] normal:aewe
        :param tuple[float] values:ew23
        :param tp.constant.SliceSource source:23ad
        :return tuple[np.array] : 2a32
        '''
        extracted_slice = tecplot.data.extract.extract_slice(
            origin=origin,
            normal=normal,
            source=source,
            dataset=self.dataset)
        nd = namedtuple('Slice', values)
        return nd(**{var : extracted_slice.values(var).as_numpy_array() for var in values})

    def _get_slices(self, origins=((0, 0, 0), (0.5, 0, 0)), normal=(1, 0, 0), values=('Y', 'U'),
                    source=tp.constant.SliceSource.VolumeZones):
        result = {x: [] for x in values}
        for origin in origins:
            extracted_slice = tecplot.data.extract.extract_slice(
                origin=origin,
                normal=normal,
                source=source,
                dataset=self.dataset)
            for var in result.keys():
                result[var].append(extracted_slice.values(var).as_numpy_array())
        nd = namedtuple('Slice', values)
        return nd(**{x : np.array(result[x]) for x in values})

    def get_slice(self, origin=(0, 0, 0), normal=(1, 0, 0), values=('Y', 'U')):
        '''
        Создает разрез плоскостью через все активные зоны,
        тип разреза по умолчанию для 3-D: объемный, для 2-D: поверхностный.

        Args:
            origin (Tuple(float)): точка, принадлежащая плоскости сечения
            normal (Tuple(float)): нормаль плоскости
            values (Tuple(str)): кортеж имен переменных, для которых требуется извлечь значения

        Returns (Tuple(np.array)): кортеж значений в соотвествии с переданным параметром values.


        '''


        if self.model_type == '2D':
            return self._get_slice(origin=origin, normal=normal, source=tp.constant.SliceSource.SurfaceZones,
                                   values=values)
        return self._get_slice(origin=origin, normal=normal, values=values)

    def get_slices(self, origins=((0, 0, 0), (0.5, 0, 0)), normal=(1, 0, 0), values=('Y', 'U')):
        '''
        Создает разрезы плоскостями через все активные зоны,
        тип разреза по умолчанию для 3-D: объемный, для 2-D: поверхностный.

        Args:
            origins (Tuple(Tuple(float))): (N, 3) - массив точек, которые задают плоскость (точка принадлежит плоскости)
            normal (Tuple(float)): общая нормаль ко всем плоскостям
            values (Tuple(str)): кортеж имен переменных, для которых требуется извлечь значения

        Returns (int): кортеж массивов значений в соотвествии с переданным параметром values.

        '''
        if self.model_type == '2D':
            return self._get_slices(origins=origins, normal=normal, source=tp.constant.SliceSource.SurfaceZones,
                                    values=values)
        return self._get_slices(origins=origins, normal=normal, values=values)

    def surface_slice(self, origin=(0, 0, 0), normal=(1, 0, 0), values=('Y', 'U')):
        return self._get_slice(origin=origin, normal=normal, source=tp.constant.SliceSource.SurfaceZones, values=values)

    def volume_slice(self, origin=(0, 0, 0), normal=(1, 0, 0), values=('Y', 'U')):
        return self._get_slice(origin=origin, normal=normal, values=values)

    def surface_slices(self, origins=((0, 0, 0), (0.5, 0, 0)), normal=(1, 0, 0), values=('Y', 'U')):
        return self._get_slices(origins=origins, normal=normal, source=tp.constant.SliceSource.SurfaceZones,
                                values=values)

    def volume_slices(self, origins=((0, 0, 0), (0.5, 0, 0)), normal=(1, 0, 0), values=('Y', 'U')):
        return self._get_slices(origins=origins, normal=normal, values=values)

    def volume_x_slice(self, cord, values=('Y', 'U')):
        return self._get_slice(origin=(cord, 0, 0), normal=(1, 0, 0), values=values)

    def volume_y_slice(self, cord, values=('Y', 'U')):
        return self._get_slice(origin=(0, cord, 0), normal=(0, 1, 0), values=values)

    def volume_z_slice(self, cord, values=('Y', 'U')):
        return self._get_slice(origin=(0, 0, cord), normal=(0, 0, 1), values=values)

    def surface_x_slice(self, cord, values=('Y', 'U')):
        return self._get_slice(origin=(cord, 0, 0), normal=(1, 0, 0), values=values,
                               source=tp.constant.SliceSource.SurfaceZones)

    def surface_y_slice(self, cord, values=('Y', 'U')):
        return self._get_slice(origin=(0, cord, 0), normal=(0, 1, 0), values=values,
                               source=tp.constant.SliceSource.SurfaceZones)

    def surface_z_slice(self, cord, values=('Y', 'U')):
        return self._get_slice(origin=(0, 0, cord), normal=(0, 0, 1), values=values,
                               source=tp.constant.SliceSource.SurfaceZones)

    def volume_x_slices(self, cords, values=('Y', 'U')):
        return self._get_slices(origins=((cord, 0, 0) for cord in cords), normal=(1, 0, 0), values=values)

    def volume_y_slices(self, cords, values=('Y', 'U')):
        return self._get_slices(origins=((0, cord, 0) for cord in cords), normal=(0, 1, 0), values=values)

    def volume_z_slices(self, cords, values=('Y', 'U')):
        return self._get_slices(origins=[(0, 0, cord) for cord in cords], normal=(0, 0, 1), values=values)

    def surface_x_slices(self, cords, values=('Y', 'U')):
        return self._get_slices(origins=((cord, 0, 0) for cord in cords), normal=(1, 0, 0), values=values,
                                source=tp.constant.SliceSource.SurfaceZones)

    def surface_y_slices(self, cords, values=('Y', 'U')):
        return self._get_slices(origins=((0, cord, 0) for cord in cords), normal=(0, 1, 0), values=values,
                                source=tp.constant.SliceSource.SurfaceZones)

    def surface_z_slices(self, cords, values=('Y', 'U')):
        return self._get_slices(origins=((0, 0, cord) for cord in cords), normal=(0, 0, 1), values=values,
                                source=tp.constant.SliceSource.SurfaceZones)

    def get_x_slice(self, cord, values=('Y', 'U')):
        return self.get_slice(origin=(cord, 0, 0), normal=(1, 0, 0), values=values)

    def get_y_slice(self, cord, values=('Y', 'U')):
        return self.get_slice(origin=(0, cord, 0), normal=(0, 1, 0), values=values)

    def get_z_slice(self, cord, values=('Y', 'U')):
        return self.get_slice(origin=(0, 0, cord), normal=(0, 0, 1), values=values)

    def get_x_slices(self, cords, values=('Y', 'U')):
        return self.get_slices(origins=((cord, 0, 0) for cord in cords), normal=(1, 0, 0), values=values)

    def get_y_slices(self, cords, values=('Y', 'U')):
        return self.get_slices(origins=((0, cord, 0) for cord in cords), normal=(0, 1, 0), values=values)

    def get_z_slices(self, cords, values=('Y', 'U')):
        return self.get_slices(origins=((0, 0, cord) for cord in cords), normal=(0, 0, 1), values=values)

    def surface_intersection(self, surface_1, surface_2, values=('Y', 'U')):
        extracted_slice_1 = tecplot.data.extract.extract_slice(
            origin=surface_1[0],
            normal=surface_1[1],
            source=tp.constant.SliceSource.VolumeZones,
            dataset=self.dataset)
        self.frame.active_zones(extracted_slice_1)
        extracted_slice_2 = tecplot.data.extract.extract_slice(
            origin=surface_2[0],
            normal=surface_2[1],
            source=tp.constant.SliceSource.SurfaceZones,
            dataset=self.dataset)
        self.frame.active_zones(self.dataset.zones())
        nd = namedtuple('SurfaceIntersection', values)
        return nd(**{var : extracted_slice_2.values(var).as_numpy_array() for var in values})

    def surfaces_intersection(self, surface_1, surfaces, values=('Y', 'U')):
        result = {x: [] for x in values}
        extracted_slice_1 = tecplot.data.extract.extract_slice(
            origin=surface_1[0],
            normal=surface_1[1],
            source=tp.constant.SliceSource.VolumeZones,
            dataset=self.dataset)
        for origin, normal in surfaces:
            self.frame.active_zones(extracted_slice_1)
            extracted_slice_2 = tecplot.data.extract.extract_slice(
                origin=origin,
                normal=normal,
                source=tp.constant.SliceSource.SurfaceZones,
                dataset=self.dataset)
            for var in result.keys():
                result[var].append(extracted_slice_2.values(var).as_numpy_array())
        self.frame.active_zones(self.dataset.zones())
        nd = namedtuple('SurfaceIntersection', values)
        return nd(**{x:np.array(result[x]) for x in values})

    def get_values(self, values=('Y', 'U', 'RHO')):
        result = {x: [] for x in values}
        for var in result.keys():
            result[var].append(self.dataset.variable(var).values(0).as_numpy_array())
        return (np.array(result[x]) for x in values)

    def close(self):
        pass
        pass

