from amuse.legacy import *
from amuse.legacy.interface.common import CommonCodeInterface

from amuse.support.units.generic_unit_system import *

import numpy

class AthenaInterface(LegacyInterface, CommonCodeInterface):
    
    include_headers = ['worker_code.h']
    
    def __init__(self, **options):
        LegacyInterface.__init__(self, **options)
        self.set_auto_decomposition(1)
        
    @legacy_function
    def par_seti():
        function = LegacyFunctionSpecification() 
        function.addParameter('block', dtype='s', direction=function.IN) 
        function.addParameter('name', dtype='s', direction=function.IN) 
        function.addParameter('fmt', dtype='s', direction=function.IN) 
        function.addParameter('ival', dtype='int32', direction=function.IN) 
        function.addParameter('comment', dtype='s', direction=function.IN) 
        function.result_type = None
        return function
        
    @legacy_function
    def par_geti():
        function = LegacyFunctionSpecification() 
        function.addParameter('block', dtype='s', direction=function.IN) 
        function.addParameter('name', dtype='s', direction=function.IN) 
        function.result_type = 'int32'
        return function
        
    @legacy_function
    def par_setd():
        function = LegacyFunctionSpecification() 
        function.addParameter('block', dtype='s', direction=function.IN) 
        function.addParameter('name', dtype='s', direction=function.IN) 
        function.addParameter('fmt', dtype='s', direction=function.IN) 
        function.addParameter('dval', dtype='float64', direction=function.IN) 
        function.addParameter('comment', dtype='s', direction=function.IN) 
        function.result_type = None
        return function
        
    @legacy_function
    def par_getd():
        function = LegacyFunctionSpecification() 
        function.addParameter('block', dtype='s', direction=function.IN) 
        function.addParameter('name', dtype='s', direction=function.IN) 
        function.result_type = 'float64'
        return function
          
    def setup_mesh(self, nmeshx, nmeshy, nmeshz, xlength, ylength, zlength):
        self.par_seti("grid", "Nx1", "%d", nmeshx, "-")
        self.par_seti("grid", "Nx2", "%d", nmeshy, "-")
        self.par_seti("grid", "Nx3", "%d", nmeshz, "-")
        
        self.par_setd("grid", "x1min", "%.15e", 0.0, "-")
        self.par_setd("grid", "x1max", "%.15e", xlength, "-")
        self.par_setd("grid", "x2min", "%.15e", 0.0, "-")
        self.par_setd("grid", "x2max", "%.15e", ylength, "-")
        self.par_setd("grid", "x3min", "%.15e", 0.0, "-")
        self.par_setd("grid", "x3max", "%.15e", zlength, "-")
        
        return 0
        
    
    def get_index_range_inclusive(self):
        """
        Returns the min and max values of indices in each
        direction. The range is inclusive, the min index
        and max index both exist and can be queried.
        The total number of cells in one direction
        is max - min + 1.
        """
        ni = self.par_geti("grid", "Nx1")
        nj = self.par_geti("grid", "Nx2")
        nk = self.par_geti("grid", "Nx3")
        return (0, ni[0]-1, 0 , nj[0]-1 , 0, nk[0]-1)
        
    def get_mesh_indices(self):
        """
        Return 3 arrays, containing the indices for i, j and k
        """
        si,ei,sj,ej,sk,ek = self.get_index_range_inclusive()
        indexgrid = numpy.mgrid[slice(si,ei+1),slice(sj,ej+1),slice(sk,ek+1)]
        return indexgrid.reshape(3, -1)
        
    
    @legacy_function    
    def get_position_of_index():
        function = LegacyFunctionSpecification()  
        function.can_handle_array = True
        for x in ['i','j','k']:
          function.addParameter(x, dtype='i', direction=function.IN)
        for x in ['x','y','z']:
          function.addParameter(x, dtype='d', direction=function.OUT)
        function.result_type = 'i'
        return function
        
    @legacy_function    
    def get_index_of_position():
        function = LegacyFunctionSpecification()  
        function.can_handle_array = True
        for x in ['x','y','z']:
          function.addParameter(x, dtype='d', direction=function.IN)
        for x in ['i','j','k']:
          function.addParameter(x, dtype='d', direction=function.OUT)
        function.result_type = 'i'
        return function
    
    @legacy_function    
    def fill_grid_state():
        function = LegacyFunctionSpecification()  
        function.can_handle_array = True
        for x in ['i','j','k']:
            function.addParameter(x, dtype='i', direction=function.IN)
        for x in ['rho','rhovx','rhovy','rhovz','en']:
            function.addParameter(x, dtype='d', direction=function.IN)
        function.result_type = 'i'
        return function
        
    
    @legacy_function    
    def get_grid_state_mpi():
        function = LegacyFunctionSpecification()  
        function.must_handle_array = True
        for x in ['i','j','k']:
            function.addParameter(x, dtype='i', direction=function.IN)
        for x in ['rho','rhovx','rhovy','rhovz','en']:
            function.addParameter(x, dtype='d', direction=function.OUT)
        function.addParameter('number_of_points', 'i', function.LENGTH)
        function.result_type = 'i'
        
        return function
        
    @legacy_function    
    def fill_grid_state_mpi():
        function = LegacyFunctionSpecification()  
        function.must_handle_array = True
        for x in ['i','j','k']:
            function.addParameter(x, dtype='i', direction=function.IN)
        for x in ['rho','rhovx','rhovy','rhovz','en']:
            function.addParameter(x, dtype='d', direction=function.IN)
        function.addParameter('number_of_points', 'i', function.LENGTH)
        function.result_type = 'i'
        return function
    
    @legacy_function    
    def get_grid_state():
        function = LegacyFunctionSpecification()  
        function.can_handle_array = True
        for x in ['i','j','k']:
            function.addParameter(x, dtype='i', direction=function.IN)
        for x in ['rho','rhovx','rhovy','rhovz','en']:
            function.addParameter(x, dtype='d', direction=function.OUT)
        function.result_type = 'i'
        return function
        
    def set_isocsound(self, value):
        self.par_setd("problem", "iso_csound", "%.15e", value, "") 
        
    def set_gamma(self, value):
        self.par_setd("problem", "gamma", "%.15e", value, "-") 
    
    def set_courant_friedrichs_lewy_number(self, value):
        self.par_setd("time", "cour_no", "%.15e", value, "-") 
        
    def set_boundary(self, xbound1, xbound2, ybound1, ybound2, zbound1, zbound2):
        map_from_string_to_flag = {"reflective": 1, "outflow":2, "periodic":4}
        
        self.par_seti("grid", "ibc_x1", "%d", map_from_string_to_flag[xbound1], "-")
        self.par_seti("grid", "obc_x1", "%d", map_from_string_to_flag[xbound2], "-")
        self.par_seti("grid", "ibc_x2", "%d", map_from_string_to_flag[ybound1], "-")
        self.par_seti("grid", "obc_x2", "%d", map_from_string_to_flag[ybound2], "-")
        self.par_seti("grid", "ibc_x3", "%d", map_from_string_to_flag[zbound1], "-")
        self.par_seti("grid", "obc_x3", "%d", map_from_string_to_flag[zbound1], "-")
    
    def set_parallel(self, nx, ny, nz):
        self.par_seti("parallel", "NGrid_x1", "%d", nx, "-")
        self.par_seti("parallel", "NGrid_x2", "%d", ny, "-")
        self.par_seti("parallel", "NGrid_x3", "%d", nz, "-")
        
    def set_auto_decomposition(self, value):
        self.par_seti("parallel", "auto", "%d", value, "-")
        
    @legacy_function    
    def initialize_grid():
        function = LegacyFunctionSpecification()  
        function.result_type = 'i'
        return function
        
    @legacy_function
    def get_timestep():
        function = LegacyFunctionSpecification() 
        function.addParameter('value', dtype='float64', direction=function.OUT) 
        function.result_type = 'i'
        return function
        
    @legacy_function
    def set_timestep():
        function = LegacyFunctionSpecification() 
        function.addParameter('value', dtype='float64', direction=function.IN) 
        function.result_type = 'i'
        return function
        
    
    @legacy_function
    def get_nghost():
        function = LegacyFunctionSpecification() 
        function.addParameter('value', dtype='int32', direction=function.OUT) 
        function.result_type = 'i'
        return function
        
    @legacy_function
    def get_time():
        function = LegacyFunctionSpecification() 
        function.addParameter('value', dtype='float64', direction=function.OUT) 
        function.result_type = 'i'
        return function
        
    @legacy_function
    def esys_roe_adb_hydro():
        function = LegacyFunctionSpecification() 
        function.addParameter('index', dtype='int32', direction=function.OUT) 
        function.addParameter('u', dtype='float64', direction=function.OUT) 
        function.addParameter('v', dtype='float64', direction=function.OUT) 
        function.addParameter('w', dtype='float64', direction=function.OUT) 
        function.addParameter('h', dtype='float64', direction=function.OUT) 
        function.addParameter('ev', dtype='float64', direction=function.OUT) 
        for i in range(5):
            function.addParameter('rem{0}'.format(i), dtype='float64', direction=function.OUT) 
        for i in range(5):
            function.addParameter('lem{0}'.format(i), dtype='float64', direction=function.OUT) 
        function.result_type = 'i'
        function.can_handle_array = True
        return function
        
    @legacy_function
    def fill_grid_linearwave_1d():
        function = LegacyFunctionSpecification() 
        function.addParameter('wave_flag', dtype='int32', direction=function.IN) 
        function.addParameter('amplitude', dtype='float64', direction=function.IN) 
        function.addParameter('vflow', dtype='float64', direction=function.IN) 
        function.addParameter('wave_dir', dtype='int32', direction=function.IN) 
        function.result_type = 'i'
        function.can_handle_array = True
        return function
        
    @legacy_function
    def evolve():
        function = LegacyFunctionSpecification() 
        function.addParameter('value', dtype='float64', direction=function.IN) 
        function.result_type = 'i'
        return function
        
        
    def get_index_range_for_potential(self):
        """
        Returns the min and max values of indices in each
        direction for the potential field, this
        range is 1 cell larger than the normal grid
        in all directions"""
        normal_range = numpy.asarray(self.get_index_range_inclusive())
        extension = (-1,1,-1,1,-1,1)
        return normal_range + extension
        
    
    @legacy_function    
    def set_potential():
        function = LegacyFunctionSpecification()  
        function.must_handle_array = True
        for x in ['i','j','k']:
            function.addParameter(x, dtype='i', direction=function.IN)
        function.addParameter('potential', dtype='d', direction=function.IN)
        function.addParameter('number_of_points', 'i', function.LENGTH)
        function.result_type = 'i'
        return function
        
    @legacy_function    
    def get_potential():
        function = LegacyFunctionSpecification()  
        function.must_handle_array = True
        for x in ['i','j','k']:
            function.addParameter(x, dtype='i', direction=function.IN)
        function.addParameter('potential', dtype='d', direction=function.OUT)
        function.addParameter('number_of_points', 'i', function.LENGTH)
        function.result_type = 'i'
        return function

        
    
class Athena(CodeInterface):

    def __init__(self, **options):
        CodeInterface.__init__(self,  AthenaInterface(**options), **options)
    
    def define_properties(self, object):
        object.add_property('get_time', time, "model_time")
        
    def define_methods(self, object):
        object.add_method(
            'evolve',
            (time,),
            (object.ERROR_CODE,),
        )
        object.add_method(
            'get_position_of_index',
            (object.INDEX, object.INDEX, object.INDEX,),
            (length, length, length, object.ERROR_CODE,)
        )
        
        density = mass / (length ** 3)
        momentum =  mass * length / time
        
        object.add_method(
            'fill_grid_state_mpi',
            (object.INDEX, object.INDEX, object.INDEX,
            density, momentum, momentum, momentum, energy),
            (object.ERROR_CODE,)
        )
        object.add_method(
            'get_grid_state_mpi',
            (object.INDEX, object.INDEX, object.INDEX,),
            (density, momentum, momentum, momentum, energy,
            object.ERROR_CODE,)
        )

        object.add_method(
            'set_potential',
            (object.INDEX, object.INDEX, object.INDEX,
            energy),
            (object.ERROR_CODE,)
        )
        object.add_method(
            'get_potential',
            (object.INDEX, object.INDEX, object.INDEX,),
            (energy,
            object.ERROR_CODE,)
        )
    
    def define_particle_sets(self, object):
        object.define_grid('grid')
        object.set_grid_range('grid', 'get_index_range_inclusive')
        object.add_getter('grid', 'get_position_of_index', names=('x','y','z'))
        object.add_getter('grid', 'get_grid_state_mpi', names=('rho', 'rhox','rhoy','rhoz','energy'))
        object.add_setter('grid', 'fill_grid_state_mpi', names=('rho', 'rhox','rhoy','rhoz','energy'))

        object.define_grid('potential_grid')
        object.set_grid_range('potential_grid', 'get_index_range_for_potential')
        object.add_getter('potential_grid', 'get_position_of_index', names=('x','y','z'))
        object.add_getter('potential_grid', 'get_potential', names=('potential',))
        object.add_setter('potential_grid', 'set_potential', names=('potential', ))
        
        
