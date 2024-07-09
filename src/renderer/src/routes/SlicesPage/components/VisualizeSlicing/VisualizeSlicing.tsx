import styles from './VisualizeSlicing.module.css'

import { Canvas, Vector3, useThree } from '@react-three/fiber'
import { OrbitControls, PerspectiveCamera } from '@react-three/drei'
import { useEffect, useMemo, useState } from 'react'
import {
	BoxGeometry,
	BufferAttribute,
	BufferGeometry,
	DoubleSide,
	Float32BufferAttribute,
	WebGLRenderer
} from 'three'
import VisualizeIcons from './components/VisualizeIcons/VisualizeIcons'

export type Point = number[]

export type Rect = {
	topLeft: Point
	topRight: Point
	bottomRight: Point
	bottomLeft: Point
}

export type BoundingBoxType = {
	min: Point
	max: Point
}

export const RAINBOW_GRADIENT = makeRainbowGradient(10)

// TODO maybe add grid

// https://github.com/We-Gold/ouroboros/blob/b67033cf3155a5ee6a3356f649b5df84d667fb6c/ouroboros/pipeline/render_slices_pipeline.py
function VisualizeSlicing({
	rects,
	boundingBoxes,
	linkRects,
	useEveryNthRect,
	colors
}: {
	rects: Rect[]
	boundingBoxes: BoundingBoxType[]
	linkRects: number[]
	useEveryNthRect?: number
	colors?: string[]
}): JSX.Element {
	if (useEveryNthRect === undefined) {
		useEveryNthRect = 1
	}

	if (colors === undefined) {
		colors = RAINBOW_GRADIENT
	}

	const boundingBoxIndicesBySliceOrder = useMemo(() => {
		let nextIndex = 0
		const indexMap = new Array(boundingBoxes.length).fill(null)

		linkRects.forEach((boundingBoxIndex) => {
			if (indexMap[boundingBoxIndex] !== null) {
				return
			}

			indexMap[boundingBoxIndex] = nextIndex++
		})

		return indexMap
	}, [boundingBoxes])

	const bounds = useMemo(
		() =>
			boundingBoxes.reduce(
				(acc, { min, max }) => {
					acc.min[0] = Math.min(acc.min[0], min[0])
					acc.min[1] = Math.min(acc.min[1], min[1])
					acc.min[2] = Math.min(acc.min[2], min[2])

					acc.max[0] = Math.max(acc.max[0], max[0])
					acc.max[1] = Math.max(acc.max[1], max[1])
					acc.max[2] = Math.max(acc.max[2], max[2])

					return acc
				},
				{
					min: [Infinity, Infinity, Infinity],
					max: [-Infinity, -Infinity, -Infinity]
				}
			),
		[boundingBoxes]
	)

	const center = [
		(bounds.min[0] + bounds.max[0]) / 2,
		(bounds.min[1] + bounds.max[1]) / 2,
		(bounds.min[2] + bounds.max[2]) / 2
	] as Vector3
	const width = bounds.max[0] - bounds.min[0]
	const height = bounds.max[1] - bounds.min[1]
	const depth = bounds.max[2] - bounds.min[2]

	// Calculate the distance required to view the entire bounding box
	// This is a simplified approach and might need adjustments based on FOV and aspect ratio
	const FOV = 50
	const maxDimension = Math.max(width, height, depth)
	const distance = maxDimension / (2 * Math.tan((Math.PI / 180) * (FOV / 2)))

	// Adjust the camera position to be centered and far enough to see everything
	// Adding some extra distance to ensure the entire bounding box is visible
	const cameraPosition = [
		center[0],
		center[1] + distance + maxDimension * 0.5,
		center[2]
	] as Vector3

	const sliceElements = useMemo(() => {
		return rects.map((rect, i) => {
			if (i % useEveryNthRect !== 0) {
				return null
			}
			const color = colors[boundingBoxIndicesBySliceOrder[linkRects[i]] % colors.length]
			return <Slice key={i} rect={rect} color={color} opacity={0.5} />
		})
	}, [rects, useEveryNthRect, colors, boundingBoxIndicesBySliceOrder, linkRects])

	const [gl, setGL] = useState<WebGLRenderer | null>(null)

	return (
		<div className={styles.visualizeSlicing}>
			<VisualizeIcons gl={gl} />
			<Canvas gl={{ preserveDrawingBuffer: true }}>
				<GLSaver setGL={setGL} />
				<PerspectiveCamera
					fov={FOV}
					makeDefault
					position={cameraPosition}
					up={[0, 0, 1]}
					far={distance + maxDimension}
				/>
				<OrbitControls target={center as Vector3} />

				{sliceElements}
				{boundingBoxes.map((boundingBox, i) => {
					return (
						<BoundingBox
							key={i}
							boundingBox={boundingBox}
							color={'white'}
							opacity={0.5}
						/>
					)
				})}
			</Canvas>
		</div>
	)
}

function GLSaver({ setGL }) {
	const gl = useThree((state) => state.gl)

	useEffect(() => {
		setGL(gl)
	}, [gl])

	return <></>
}

function BoundingBox({
	boundingBox,
	color,
	opacity
}: {
	boundingBox: BoundingBoxType
	color: string
	opacity: number
}): JSX.Element {
	const { min, max } = boundingBox
	const width = max[0] - min[0]
	const height = max[1] - min[1]
	const depth = max[2] - min[2]

	const position = useMemo(
		() => [min[0] + width / 2, min[1] + height / 2, min[2] + depth / 2] as Vector3,
		[boundingBox]
	)

	const geometry = useMemo(() => new BoxGeometry(width, height, depth), [boundingBox])

	return (
		<mesh position={position}>
			<lineSegments>
				<edgesGeometry attach="geometry" args={[geometry]} />
				<lineBasicMaterial opacity={opacity} color={color} linewidth={3} />
			</lineSegments>
		</mesh>
	)
}

function Slice({
	rect,
	color,
	opacity
}: {
	rect: Rect
	color: string
	opacity: number
}): JSX.Element {
	const geometry = useMemo(() => {
		const vertices = new Float32Array([
			...rect.topRight,
			...rect.topLeft,
			...rect.bottomLeft,
			...rect.bottomRight
		])

		const geom = new BufferGeometry()
		const indices = new Uint16Array([0, 1, 2, 2, 3, 0])

		geom.setAttribute('position', new Float32BufferAttribute(vertices, 3))
		geom.setIndex(new BufferAttribute(indices, 1))
		geom.computeVertexNormals()

		return geom
	}, [rect])

	return (
		<>
			<mesh geometry={geometry}>
				<meshBasicMaterial
					transparent={true}
					opacity={opacity}
					color={color}
					side={DoubleSide}
				/>
				<lineSegments>
					<edgesGeometry attach="geometry" args={[geometry]} />
					<lineBasicMaterial color={'black'} linewidth={3} />
				</lineSegments>
			</mesh>
		</>
	)
}

function makeRainbowGradient(numColors = 10) {
	const gradient: string[] = []

	// Make a rainbow gradient with HSL
	for (let i = 0; i < numColors; i++) {
		const hue = i / numColors
		gradient.push(`hsl(${hue * 360}, 100%, 50%)`)
	}

	return gradient
}

export default VisualizeSlicing
