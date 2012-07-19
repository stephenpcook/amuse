from amuse.community import *
from amuse.community.interface.gd import GravitationalDynamicsInterface
from amuse.community.interface.gd import GravitationalDynamics

class HuaynoInterface(CodeInterface, LiteratureReferencesMixIn, GravitationalDynamicsInterface):
    """
    N-body integration module with individual and variable time step
    using the Hermite integration scheme.

    .. [#] Pelupessy, I.F., XXX, Portegies Zwart, S.F., to be submitted
    """
    include_headers = ['worker_code.h']
    
    MODE_OPENCL='opencl'
    MODE_OPENMP='openmp'
        
    def name_of_worker(self,mode):
        if mode==self.MODE_OPENCL:
            return 'huayno_worker_cl'
        if mode==self.MODE_OPENMP:
            return 'huayno_worker_mp'
        return 'huayno_worker'
      
    def __init__(self, mode=None, **options):
        CodeInterface.__init__(self, name_of_the_worker = self.name_of_worker(mode), **options) 

    @legacy_function      
    def get_time():
        function = LegacyFunctionSpecification()
        function.addParameter('time', dtype='d', direction=function.OUT)
        function.result_type = 'i'
        return function


    @legacy_function      
    def commit_particles():
        function = LegacyFunctionSpecification()
        function.result_type = 'i'
        return function

    @legacy_function      
    def get_kinetic_energy():
        function = LegacyFunctionSpecification()
        function.addParameter('kinetic_energy', dtype='d', direction=function.OUT)
        function.result_type = 'i'
        return function

    @legacy_function      
    def get_potential_energy():
        function = LegacyFunctionSpecification()
        function.addParameter('potential_energy', dtype='d', direction=function.OUT)
        function.result_type = 'i'
        return function

    @legacy_function      
    def initialize_code():
        function = LegacyFunctionSpecification()
        function.result_type = 'i'
        return function

    @legacy_function    
    def evolve_model():
        function = LegacyFunctionSpecification()  
        function.addParameter('time_end', dtype='d', direction=function.IN)
        function.result_type = 'i'
        return function

    @legacy_function      
    def get_timestep_parameter():
        function = LegacyFunctionSpecification()
        function.addParameter('time_param', dtype='d', direction=function.OUT)
        function.result_type = 'i'
        return function

    @legacy_function      
    def set_timestep_parameter():
        function = LegacyFunctionSpecification()
        function.addParameter('time_param', dtype='d', direction=function.IN)
        function.result_type = 'i'
        return function

    @legacy_function      
    def get_timestep():
        function = LegacyFunctionSpecification()
        function.addParameter('timestep', dtype='d', direction=function.OUT)
        function.result_type = 'i'
        return function

    @legacy_function      
    def set_timestep():
        function = LegacyFunctionSpecification()
        function.addParameter('timestep', dtype='d', direction=function.IN)
        function.result_type = 'i'
        return function

    @legacy_function      
    def get_number_of_particles():
        function = LegacyFunctionSpecification()
        function.addParameter('number_of_particles', dtype='i', direction=function.OUT)
        function.result_type = 'i'
        return function

    @legacy_function      
    def get_inttype_parameter():
        function = LegacyFunctionSpecification()
        function.addParameter('inttype', dtype='i', direction=function.OUT)
        function.result_type = 'i'
        return function

    @legacy_function      
    def set_inttype_parameter():
        function = LegacyFunctionSpecification()
        function.addParameter('inttype', dtype='i', direction=function.IN)
        function.result_type = 'i'
        return function

    @legacy_function      
    def get_eps2_parameter():
        function = LegacyFunctionSpecification()
        function.addParameter('eps2', dtype='d', direction=function.OUT)
        function.result_type = 'i'
        return function

    @legacy_function      
    def set_eps2_parameter():
        function = LegacyFunctionSpecification()
        function.addParameter('eps2', dtype='d', direction=function.IN)
        function.result_type = 'i'
        return function

    def set_eps2(self, e):
        return self.set_eps2_parameter(e)

    def get_eps2(self):
        return self.get_eps2_parameter()
    
class Huayno(GravitationalDynamics):

    class inttypes(object):
        # http://stackoverflow.com/questions/36932/whats-the-best-way-to-implement-an-enum-in-python
        SHARED2=1
        EXTRAPOLATE=5
        PASS_KDK=2
        PASS_DKD=7
        HOLD_KDK=3
        HOLD_DKD=8
        PPASS_DKD=9
        BRIDGE_KDK=4
        BRIDGE_DKD=10
        CC=11
        CC_KEPLER=12
        OK=13
#        KEPLER=14
        SHARED4=15
        SHARED6=18
        SHARED8=19
        SHARED10=20
        SHAREDBS=21
        
        @classmethod
        def _list(cls):
              return set([x for x in cls.__dict__.keys() if not x.startswith('_')])
    

    def __init__(self, convert_nbody = None, **options):
        legacy_interface = HuaynoInterface(**options)
#        self.legacy_doc = legacy_interface.__doc__

        GravitationalDynamics.__init__(
            self,
            legacy_interface,
            convert_nbody,
            **options
        )

    def define_parameters(self, object):
        object.add_method_parameter(
            "get_eps2",
            "set_eps2", 
            "epsilon_squared", 
            "smoothing parameter for gravity calculations", 
            default_value = 0.0 | nbody_system.length * nbody_system.length
        )

        object.add_method_parameter(
            "get_timestep_parameter",
            "set_timestep_parameter", 
            "timestep_parameter", 
            "timestep parameter for gravity calculations", 
            default_value = 0.03
        )

        object.add_method_parameter(
            "get_timestep",
            "set_timestep", 
            "timestep", 
            "timestep for evolve calls", 
            default_value = 0.0 | nbody_system.time
        )


        object.add_method_parameter(
            "get_inttype_parameter",
            "set_inttype_parameter", 
            "inttype_parameter", 
            "integrator method to use", 
            default_value = 8
        )

        object.add_method_parameter(
            "get_begin_time",
            "set_begin_time",
            "begin_time",
            "model time to start the simulation at",
            default_value = 0.0 | nbody_system.time
        )



    def define_methods(self, object):
        GravitationalDynamics.define_methods(self, object)
        
        object.add_method(
            "get_eps2",
            (),
            (nbody_system.length * nbody_system.length, object.ERROR_CODE,)
        )
        
        object.add_method(
            "set_eps2",
            (nbody_system.length * nbody_system.length, ),
            (object.ERROR_CODE,)
        )
        
        object.add_method(
            "get_timestep_parameter",
            (),
            (object.NO_UNIT, object.ERROR_CODE,)
        )
        
        object.add_method(
            "set_timestep_parameter",
            (object.NO_UNIT, ),
            (object.ERROR_CODE,)
        )

        object.add_method(
            "get_timestep",
            (),
            (nbody_system.time, object.ERROR_CODE,)
        )
        
        object.add_method(
            "set_timestep",
            (nbody_system.time, ),
            (object.ERROR_CODE,)
        )

        
        object.add_method(
            "get_inttype_parameter",
            (),
            (object.NO_UNIT, object.ERROR_CODE,)
        )
        
        object.add_method(
            "set_inttype_parameter",
            (object.NO_UNIT, ),
            (object.ERROR_CODE,)
        )
        
    def define_particle_sets(self, object):
        GravitationalDynamics.define_particle_sets(self, object)

    def define_state(self, object):
        GravitationalDynamics.define_state(self, object)
        
        object.add_method('RUN', 'get_kinetic_energy')
        object.add_method('RUN', 'get_potential_energy')
