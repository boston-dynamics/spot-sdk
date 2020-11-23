#version 130

uniform mat4 camera1_MVP;
varying vec4 position_wrt_camera1_mvp;

uniform mat4 camera2_MVP;
varying vec4 position_wrt_camera2_mvp;

void main() {    
    gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;

    vec4 position_wrt_vo = gl_Vertex;

    position_wrt_camera1_mvp = camera1_MVP * position_wrt_vo;
    position_wrt_camera2_mvp = camera2_MVP * position_wrt_vo;
}