<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Service Customization
Spot 3.3 release features a new system for parameterizing 3rd party services.  If your service has a knob that needs wiggling by a user, your service can advertise a parameter, Boston Dynamics clients will display that knob, and users will be able to wiggle it.  Services that opt into this feature will get:
- UI on the Tablet application for actions containing parameters (either when recording a mission, or just performing actions in teleoperation).
- UI on the Tablet application for adjusting image parameters when streaming from a 3rd party image source.
- UI on Scout for editing any autowalk action with parameters.


The following services support service customization:


* `Image` services.
* `Data Acquisition Plugin` services.
* `Network Compute Bridge Worker` services.
* `Remote Mission` services.
* `Area Callback` services.


The service customization system supports several different primitive types, and hierarchical containers - it's powerful.  All first class Boston Dynamics inspections, including our 3.3 thermal inspection (shown below), are built using the same service customization system that's available to developers:


![Tablet Screenshot](./images/service_customization_thermal.jpg)


## Service Customization Language


### Spec
A specification, or spec, is what services advertises to clients so that the client can build a UI.  It's how services encode what parameters that service expects - "I need a slider from 0 to 100" or "I need two sliders and a checkbox".  The root level of any service spec is a dictionary so that parameters can be added in the future with ease.


### Parameter
Parameters are instantiations of Specs.  Where a spec says: "I need a slider from 0 to 100 titled threshold", a parameter says "threshold: 58".  It's result of a spec after it's been turned into a UI, and a user has wiggled knobs.


## Parameter Types


### Double
The double parameter allows users to enter a floating point number.  It is defined by the `DoubleParam` and `DoubleParam.Spec`  protobuf messages.  The spec for doubles allows developers to set a _min value_, and a _max value_.  The UI element displayed will differ based on the contents of _min value_ and _max value_.  If both are set, the UI will provide a slider AND a numerical textbox users can type values into, otherwise, the UI will display just a numerical textbox.  `DoubleParam.Spec` also allows developers to specify units, which we'll talk about in a second.


### Int
The int parameter is identical to the double parameter, but everything is an integer.  It is defined by the `Int64Param` and `Int64Param.Spec`  protobuf messages.


### Units for Int & Double
Both int and double allow developers to specify units.  Units will show up on the UI next to the specified value; a units string of "%" will cause the UI to render "32%".  If developers specify one of the first class unit enums, temperature or pressure, clients will automatically convert units to match the users preference, and do the conversion for the service.


For example, imagine a service that wants a temperature parameter between 0&deg;C and 100&deg;C.  If the service specified the limits of 0 - 100, and the units as `TEMPERATURE_CELSIUS`, clients will either show that as 32&deg;F to 212&deg;F or 0&deg;C to 100&deg;C, depending on the users unit preferences.  Either way, the client will pack in the specified value as Celsius.  **The service can assume all values are in Celsius, because they will be.**  Also note that the units proto includes an *is_relative* flag, which allows developers to specify if they want the client to respect a zero point offset between units.  This mostly helps to differentiate absolute and relative temperatures.  If ensuring an object is no hotter than a specific temperature, 0&deg;C - 100&deg;C should map to 32&deg;F to 212&deg;F (what happens when *is_relative* is set to false).  If ensuring that two objects are no more than X degrees apart, 0&deg;C - 100&deg;C should map to 0&deg;F to 180&deg;F  (what happens when *is_relative* is set to true).  Note that 0 C now maps to 0 F.


### String
The string parameter allows users to specify a string.  It is defined by the `StringParam` and `StringParam.Spec` protobuf messages.  A string spec can be used to let a user: (1) pick from a set of predefined options, (2) type in their own free form string, or (3) both.  Predefined options are specified using the _options_ field, and whether or not the user is allowed to type in their own option is controlled by the _editable_ flag.  Strings will be represented in the client UI by either a switch, a set of radio buttons, or a combo box, depending on how many options are present.


### Bool
The bool parameter allows users to turn things on and off.  It is defined by the `BoolParam` and `BoolParam.Spec` protobuf messages.  It will be represented in the UI by a checkbox.


### Region of Interest
Region of Interest, or ROI, allows users to specify a region of an image.  It is defined by the `RegionOfInterestParam` and `RegionOfInterestParam.Spec` protobuf messages.  As of 3.3, ROI params are limited to specifying rectangular regions, and really only work well for `Network Compute Bridge Worker` services.  The tablet does not allow setting ROI for `Area Callback` services, but that will likely change in the future.  Other services have limited ROI functionality.


Region of interest is helpful to narrow down a search space if there is a lot going on in an image, and the camera can't be moved or zoomed in such a way that only the thing the user care's about is in frame.  Users will be able to draw regions on live images using the tablet UI, and on images taken at record time when editing parameters in Scout.


### Dictionary
Dictionary is the first container type, and is defined by the `DictParam` and `DictParam.Spec` protobuf messages.  Dictionaries allow users to specify many named children of various types: string, ints, dictionaries, etc.  Note: primitives themselves don't contain a name, but their entries inside containers do.  Each child of a dictionary is required to have a _key_ string, which services will use to find particular values.  Changing a _key_ has consequences for backwards compatibility, so there is a second ephemeral name field embedded into `UserInterfaceInfo` called *display_name*.  *display_name* exists so it can be changed at any time, without consequence.  If no *display_name* is specified, _key_ will be used.


UI's will always allow users to specify every child of a dictionary.  Each child is independent.  Dictionaries can be told to start collapsed, which is a great way to hide advanced parameters for your inspections that most users won't wiggle.


### One-Of
One-Of is another container type, and is defined by the `OneOfParam` and `OneOfParam.Spec` protobuf messages.  Unlike dictionary, One-Of will only let the users specify a single child at a time.  The UI will allow users to pick which child they want to specify, and allow users to specify that child.  Note that the child can be completely empty.  One-Of's are a great way to encode optional parameters, or parameters that only exist under circumstances.  It is valid to have an empty One-Of child - that just means that if selected, that option has no additional parameters.


Like dictionary children, one-of children also contain a `UserInterfaceInfo`, which allows developers to both order elements in a deterministic way, and override what string the UI uses to represent the child.  One-Of specs are constrained to ONLY contain dictionary children.


### List
List is the final container type, and is defined by the `ListParam` and `ListParam.Spec` protobuf messages.  Lists must be homogenous, meaning each child in the list must meet the same spec.


### Custom Param
The `CustomParam` and `CustomParam.Spec` protobuf messages are container types for the various parameter types.  A custom param can either be a double, or a bool, or an int, or a dictionary, etc.  Both dictionaries and list children contain a CustomParam.


## Example Specifications

For a single specification of "param B", which is a double representing temperature with a default value 40 and max value of 101.5, the DictParam.Spec is:

```
specs {
  key: "param_b"
  value {
    spec {
      double_spec {
        default_value {
          value: 40.0
        }
        units {
          temp: TEMPERATURE_CELSIUS
        }
        min_value {
        }
        max_value {
          value: 101.5
        }
      }
    }
    ui_info {
      display_name: "Param B"
    }
  }
}
```

To specify a 1-3 element list of string/int tuples, where each string must be either 'A', 'B', or 'C' and the int between 0 and 9, the DictParam.Spec is:

```
specs {
  key: "list_of_tuples"
  value {
    spec {
      list_spec {
        element_spec {
          dict_spec {
            specs {
              key: "param_a"
              value {
                spec {
                  string_spec {
                    options: "A"
                    options: "B"
                    options: "C"
                  }
                }
                ui_info {
                  display_name: "Param A"
                  display_order: 1
                }
              }
            }
            specs {
              key: "param_b"
              value {
                spec {
                  int_spec {
                    default_value {
                      value: 5
                    }
                    units {
                      name: "Apples"
                    }
                    min_value {
                    }
                    max_value {
                      value: 9
                    }
                  }
                }
                ui_info {
                  display_name: "Param B"
                  display_order: 2
                }
              }
            }
          }
        }
        min_number_of_values {
          value: 1
        }
        max_number_of_values {
          value: 3
        }
      }
    }
    ui_info {
      display_name: "List of Tuples"
    }
  }
}
```


Let's take another look at the 3.3 boston dynamic thermal inspection:


![Tablet Screenshot](./images/service_customization_thermal.jpg)


The UI on the left is generated with service customization.  The spec provided for the thermal NCB worker looks like this:


- A root level dictionary, containing:
   - "Relative threshold", a one-of with two children:
       - "Off" - a dictionary with no child parameters
       - "On" - a dictionary with child parameters:
           - "Threshold" - a double param with temperature units and minimum value 0, and *is_relative* set to true.
   - A list, containing 1-3 children that meet the spec:
       - Dictionary, containing:
           - "Region" - a region of interest on a thermal image.
           - "Max Alarm Threshold", a one-of with two children:
               - "Off" - a dictionary with no child parameters
               - "On" - a dictionary with child parameters:
                   - "Threshold" - a double param with temperature units and *is_relative* set to false.
           - "Min Alarm Threshold", a one-of with two children:
               - "Off" - a dictionary with no child parameters
               - "On" - a dictionary with child parameters:
                   - "Threshold" - a double param with temperature units and *is_relative* set to false.


## Implementing Service Customization


### **Image** services
- Specs: specs need to be returned by the `ListImageSourcesResponse` rpc, inside the `ImageSource` protobuf message.
- Parameters: parameters are sent to the service as part of the `GetImage` rpc, inside the `ImageRequest` protobuf message.
- Example: see the [custom_parameter_image_server](../../python/examples/service_customization/custom_parameter_image_server/README.md) python example.


### **Network Compute Bridge Worker** services
- Specs: specs need to be returned by the `ListAvailableModels` rpc, inside the `ModelData` protobuf message.
- Parameters: parameters are sent to the service as part of the `WorkerCompute` rpc, inside the `ComputeParameters` protobuf message.
- Example: see the [custom_parameter_ncb_worker](../../python/examples/service_customization/custom_parameter_ncb_worker/README.md) python example.


### **Remote Mission** services
- Specs: specs need to be returned by the `GetRemoteMissionServiceInfo` rpc, inside the `GetRemoteMissionServiceInfoResponse` protobuf message.
- Parameters: parameters are sent to the service as part of the `Tick` rpc, inside the `TickRequest` protobuf message.
- Example: see the [hello_world_mission_service](../../python/examples/remote_mission_service/README.md) python example.


### **Area Callback** services
- Specs: specs need to be returned by the `AreaCallbackInformation` rpc, inside the `AreaCallbackInformation` protobuf message.
- Parameters: parameters are sent to the service as part of the `BeginCallback` rpc, inside the `BeginCallbackRequest` protobuf message.
- No example available.

## Parameter Coercion
Coercion allows you to gracefully handle errors in your parameters. If the parameter provided from the server is out of spec, it can be coerced to be in spec.

Given a `StringSpec`:
```
string_spec {
    options: "A"
    options: "B"
    options: "C"
}
```
If the parameter came back with a value `D`, this would be considered out of spec.
```python
>>> from bosdyn.client.service_customization_helpers import string_param_coerce_to, make_string_param_spec
>>> from bosdyn.api.service_customization_pb2 import StringParam
>>> spec = make_string_param_spec(options=['A', 'B', 'C'], default_value='B')
>>> param = StringParam(value='D')
>>> param
value: 'D'
>>> string_param_coerce_to(spec, param)
True
>>> param
value: 'B'
```
The parameter is modified in-place - a new parameter does not get returned. An example demonstrating coercion can be found in the [hello_world_mission_service](../../python/examples/remote_mission_service/README.md) python example.

Each coercion function returns a boolean indicating whether any field was modified to be in spec. It is not specified which precise field(s) may have been modified.
