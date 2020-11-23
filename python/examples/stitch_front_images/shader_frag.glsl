#version 130

// Color the projection plane should be in regions that no images cover.
uniform vec4 backColor;

varying vec4 position_wrt_camera1_mvp;
uniform sampler2D image1;

varying vec4 position_wrt_camera2_mvp;
uniform sampler2D image2;

// When to images overlap, we blend them together.  blendingPower controls how aggresive the
// blending window is.  blendingPower of Infinity would be no blending (hard cut line between
// images).  blendingPower of 0 would mean equal weights always applied to information from both
// cameras.  blendingMinimum is more of a helper number to prevent numerial overflow.
const float blendingMinimum = 0.001;
const float blendingPower = 10.0;

// How far was this point from the center of the camera image?? This will be used to determine
// how the information retrieved from the image will be blended with other images.
float calculateScore(vec2 imageLocation) {
    vec2 locationNormalized = imageLocation * 2.0 - 1.0; // -1 to 1 (left to right up to down)
    locationNormalized = 1.0 - abs(locationNormalized);  // 0.01s on border, 1s in centers
    if (min(locationNormalized.x, locationNormalized.y) < 0.0) {
        return 0.0;
    }

    float score = mix(locationNormalized.x * locationNormalized.y, 1.0, blendingMinimum);
    // 0.001 on border, 1.0 in middle
    // contour lines are ellipses

    return pow(score, blendingPower);
}

vec2 calculateImageLocation(vec4 xyz1, out float weight) {
    if (xyz1.z <= 0.0) {
        // Behind camera!
        weight = 0.0;
        return vec2(0.0, 0.0);
    } else {
        // When you multiply an XYZ location by a projection matrix, you need to divide resultant X and Y
        // by Z to get pixel coordinates U and V
        vec2 location = (xyz1.xy / xyz1.z); // should return pixel coordinate u v on scale of 0 to 1

        weight = calculateScore(location);
        return location;
    }
}

void main()
{
    float totalWeight = 0.0;

    float image1Weight;
    vec2 image1Location = calculateImageLocation(position_wrt_camera1_mvp, image1Weight);
    vec4 image1Color = texture(image1, image1Location);
    totalWeight += image1Weight;

    float image2Weight;
    vec2 image2Location = calculateImageLocation(position_wrt_camera2_mvp, image2Weight);
    vec4 image2Color = texture(image2, image2Location);
    totalWeight += image2Weight;

    if (totalWeight == 0.0) {

        gl_FragColor = backColor;

    } else {

        gl_FragColor = vec4(0.0);

        image1Weight /= totalWeight;
        gl_FragColor += image1Color * image1Weight;

        image2Weight /= totalWeight;
        gl_FragColor += image2Color * image2Weight;

    }
}