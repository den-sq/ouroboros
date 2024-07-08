import styles from './VisualizeSlicing.module.css'

import { Canvas, Vector3 } from '@react-three/fiber'
import { OrbitControls, PerspectiveCamera } from '@react-three/drei'
import { useMemo } from 'react'
import {
	BoxGeometry,
	BufferAttribute,
	BufferGeometry,
	DoubleSide,
	Float32BufferAttribute
} from 'three'

export type Point = [number, number, number]

export type Rect = {
	topLeft: Point
	topRight: Point
	bottomRight: Point
	bottomLeft: Point
}

export type BoundingBox = {
	min: Point
	max: Point
}

const colors = ['red', 'orange', 'yellow', 'green', 'blue', 'purple']

// https://github.com/We-Gold/ouroboros/blob/b67033cf3155a5ee6a3356f649b5df84d667fb6c/ouroboros/pipeline/render_slices_pipeline.py
function VisualizeSlicing({
	rects,
	boundingBoxes,
	linkRects
}: {
	rects: Rect[]
	boundingBoxes: BoundingBox[]
	linkRects: number[]
}): JSX.Element {
	return (
		<div className={styles.visualizeSlicing}>
			<Canvas>
				<PerspectiveCamera makeDefault position={[0, 0, 10]} />
				<OrbitControls />
				<ambientLight intensity={0.1} />
				<directionalLight color="white" position={[0, 0, 5]} />
				{rects.map((rect, i) => {
					const color = colors[linkRects[i] % colors.length]
					return <Slice key={i} rect={rect} color={color} opacity={0.3} />
				})}
				{boundingBoxes.map((boundingBox, i) => {
					const color = colors[i % colors.length]
					return <BoundingBox key={i} boundingBox={boundingBox} color={color} />
				})}
				<axesHelper args={[5]} />
			</Canvas>
		</div>
	)
}

function BoundingBox({
	boundingBox,
	color
}: {
	boundingBox: BoundingBox
	color: string
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
				<lineBasicMaterial attach="material" linewidth={3} />
			</lineSegments>
			<meshBasicMaterial color={color} />
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
		<mesh geometry={geometry}>
			<meshBasicMaterial opacity={opacity} color={color} side={DoubleSide} />
		</mesh>
	)
}

export default VisualizeSlicing
