import { useLayoutEffect } from 'react'
import { useThree } from '@react-three/fiber'
import * as THREE from 'three'

/**
 * Процедурное IBL-окружение для PBR-отражений.
 * Собирается один раз через PMREMGenerator и всегда сбрасывает render target
 * в null — в отличие от <Environment> из drei, который в headless-прогоне
 * оставлял target привязанным и уводил всю сцену в cubemap.
 */
export function ProceduralEnv({ intensity = 1 }: { intensity?: number }) {
  const gl = useThree((s) => s.gl)
  const scene = useThree((s) => s.scene)

  useLayoutEffect(() => {
    const pmrem = new THREE.PMREMGenerator(gl)
    pmrem.compileEquirectangularShader()

    const envScene = new THREE.Scene()

    // холодный «лунный» купол сверху
    const skyGeo = new THREE.SphereGeometry(60, 24, 16)
    const skyMat = new THREE.ShaderMaterial({
      side: THREE.BackSide,
      uniforms: {},
      vertexShader: `varying vec3 vP; void main(){ vP = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
      fragmentShader: `
        varying vec3 vP;
        void main(){
          float h = normalize(vP).y;
          vec3 top = vec3(0.004, 0.007, 0.018);
          vec3 mid = vec3(0.008, 0.013, 0.028);
          vec3 hor = vec3(0.022, 0.024, 0.034);
          vec3 c = h > 0.0 ? mix(hor, mix(mid, top, smoothstep(0.0, 0.6, h)), smoothstep(0.0, 0.35, h))
                           : mix(hor, vec3(0.003, 0.003, 0.005), smoothstep(0.0, -0.4, h));
          gl_FragColor = vec4(c, 1.0);
        }`,
    })
    envScene.add(new THREE.Mesh(skyGeo, skyMat))

    // тёплые источники — дают оранжевые блики на мокром асфальте и латуни
    const warm = new THREE.MeshBasicMaterial({ color: new THREE.Color(0xffb35c).multiplyScalar(9) })
    for (const [x, y, z, s] of [
      [7, 3.4, 5, 2.4],
      [-7, 3.4, 5, 2.0],
      [0, 3.2, -8, 2.2],
    ] as const) {
      const bulb = new THREE.Mesh(new THREE.SphereGeometry(s, 12, 10), warm)
      bulb.position.set(x, y, z)
      envScene.add(bulb)
    }

    // холодный ключ (луна)
    const moon = new THREE.Mesh(
      new THREE.SphereGeometry(6, 16, 12),
      new THREE.MeshBasicMaterial({ color: new THREE.Color(0xa8c4f0).multiplyScalar(4.5) }),
    )
    moon.position.set(-16, 22, -12)
    envScene.add(moon)

    const target = pmrem.fromScene(envScene, 0.04)
    scene.environment = target.texture
    scene.environmentIntensity = intensity

    // гарантированный сброс состояния рендера
    gl.setRenderTarget(null)
    gl.shadowMap.needsUpdate = true

    return () => {
      scene.environment = null
      target.dispose()
      pmrem.dispose()
      skyGeo.dispose()
      skyMat.dispose()
      warm.dispose()
      gl.setRenderTarget(null)
    }
  }, [gl, scene, intensity])

  return null
}
