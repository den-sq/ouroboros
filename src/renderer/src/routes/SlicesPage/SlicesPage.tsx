import OptionsPanel from '@renderer/components/OptionsPanel/OptionsPanel'
import styles from './SlicesPage.module.css'
import VisualizePanel from '@renderer/components/VisualizePanel/VisualizePanel'
import ProgressPanel from '@renderer/components/ProgressPanel/Progress'
import { ServerContext } from '@renderer/contexts/ServerContext'
import {
	CompoundEntry,
	CompoundValueType,
	Entry,
	SliceOptionsFile
} from '@renderer/interfaces/options'
import { useContext, useEffect, useState } from 'react'
import { DirectoryContext } from '@renderer/contexts/DirectoryContext'
import { join, readFile, writeFile } from '@renderer/interfaces/file'
import { AlertContext } from '@renderer/contexts/AlertContext'
import VisualizeSlicing from './components/VisualizeSlicing/VisualizeSlicing'
import SliceResultSchema from '@renderer/schemas/slice-result-schema'
import { safeParse } from 'valibot'
import SliceStatusResultSchema from '@renderer/schemas/slice-status-result-schema'
import NeuroglancerJSONSchema from '@renderer/schemas/neuroglancer-json-schema'
import SliceVisualizationResultSchema from '@renderer/schemas/slice-visualization-result-schema'
import ConfigurationJSONSchema, {
	ConfigurationJSON
} from '@renderer/schemas/configuration-json-schema'
import { DragContext } from '@renderer/contexts/DragContext'
import { useDroppable } from '@dnd-kit/core'

const SLICE_RENDER_PROPORTION = 0.01

const SLICE_STREAM = '/slice_status_stream/'

const SLICE_STEP_NAME = 'SliceParallelPipelineStep'

function SlicesPage(): JSX.Element {
	const {
		progress,
		boundingBoxProgress,
		connected,
		entries,
		onSubmit,
		visualizationData,
		onEntryChange,
		onHeaderDrop,
		setDropNodeRef,
		isOver
	} = useSlicePageState()

	return (
		<div className={styles.slicePage}>
			<div ref={setDropNodeRef} style={{ position: 'relative' }}>
				{isOver ? (
					<svg
						xmlns="http://www.w3.org/2000/svg"
						viewBox="0 0 448 512"
						width="40px"
						style={{
							position: 'absolute',
							top: '50%',
							left: '50%',
							transform: 'translate(-50%, -50%)',
							zIndex: '1000'
						}}
					>
						<path
							fill="white"
							d="M256 80c0-17.7-14.3-32-32-32s-32 14.3-32 32l0 144L48 224c-17.7 0-32 14.3-32 32s14.3 32 32 32l144 0 0 144c0 17.7 14.3 32 32 32s32-14.3 32-32l0-144 144 0c17.7 0 32-14.3 32-32s-14.3-32-32-32l-144 0 0-144z"
						/>
					</svg>
				) : null}
				<VisualizePanel>
					{visualizationData ? (
						<VisualizeSlicing
							{...visualizationData}
							useEveryNthRect={Math.floor(
								visualizationData.rects.length * SLICE_RENDER_PROPORTION
							)}
							bboxPercent={boundingBoxProgress}
						/>
					) : null}
				</VisualizePanel>
			</div>
			<ProgressPanel progress={progress} connected={connected} />
			<OptionsPanel
				entries={entries}
				onSubmit={onSubmit}
				onEntryChange={onEntryChange}
				onHeaderDrop={onHeaderDrop}
			/>
		</div>
	)
}

type SlicePageState = {
	progress: [string, number][]
	boundingBoxProgress: number
	connected: boolean
	entries: (Entry | CompoundEntry)[]
	onSubmit: () => Promise<void>
	visualizationData: VisualizationOutput | null
	onEntryChange: (entry: Entry) => Promise<void>
	onHeaderDrop: (content: string) => Promise<void>
	setDropNodeRef: (node: HTMLElement | null) => void
	isOver: boolean
}

function useSlicePageState(): SlicePageState {
	const {
		connected,
		performFetch,
		useFetchListener,
		performStream,
		useStreamListener,
		clearFetch,
		clearStream
	} = useContext(ServerContext)
	const { directoryPath } = useContext(DirectoryContext)

	const [entries, setEntries] = useState<(Entry | CompoundEntry)[]>([new SliceOptionsFile()])

	const { addAlert } = useContext(AlertContext)

	const [progress, setProgress] = useState<[string, number][]>([])

	const { results: sliceResults } = useFetchListener('/slice/')
	const {
		results: streamResults,
		error: streamError,
		done: streamDone
	} = useStreamListener(SLICE_STREAM)

	const [visualizationData, setVisualizationData] = useState<VisualizationOutput | null>(null)

	const { results: onDemandVisualizationResults } = useFetchListener(
		'/create_slice_visualization/'
	)

	const { clearDragEvent, parentChildData } = useContext(DragContext)
	const { isOver, setNodeRef: setDropNodeRef } = useDroppable({
		id: 'slice-visualize'
	})

	////// HANDLE CONFIGURATION JSON FILE DROP ONTO VISUALIZATION PANEL //////
	useEffect(() => {
		const handleDrop = async (): Promise<void> => {
			if (parentChildData) {
				const item = parentChildData[1]

				if (
					item.data.current?.source === 'file-explorer' &&
					parentChildData[0].toString() === 'slice-visualize'
				) {
					// Check if the file is a JSON file
					if (!item.data.current.name.endsWith('.json')) {
						addAlert(
							'Invalid JSON file. Only -configuration.json files are currently supported for visualization.',
							'error'
						)
						return
					}

					// Read the JSON file
					readFile('', item.id.toString()).then((data) => {
						let json = null

						try {
							json = JSON.parse(data)
						} catch (e) {
							addAlert(
								'Invalid JSON file. Only -configuration.json files are currently supported for visualization.',
								'error'
							)
							return
						}

						const jsonResult = safeParse(ConfigurationJSONSchema, json)

						if (jsonResult.success) {
							const data = convertConfigJSONToProps(jsonResult.output)

							setVisualizationData(data)
						}
					})

					// Clear the drag event
					clearDragEvent()
				}
			}
		}

		handleDrop()
	}, [isOver, parentChildData])

	// Update the visualization data when new data is received
	useEffect(() => {
		const visualizationDataResult = safeParse(
			SliceVisualizationResultSchema,
			onDemandVisualizationResults
		)

		if (visualizationDataResult.success) {
			setVisualizationData(visualizationDataToProps(visualizationDataResult.output.data))
		}
	}, [onDemandVisualizationResults])

	// Listen to the status stream for the active task
	useEffect(() => {
		const results = safeParse(SliceResultSchema, sliceResults)

		if (results.success) {
			performStream(SLICE_STREAM, results.output)
		}
	}, [sliceResults])

	// Update the progress state when new data is received
	useEffect(() => {
		const results = safeParse(SliceStatusResultSchema, streamResults)

		if (results.success && !results.output.error) {
			setProgress(results.output.progress)
		}
	}, [streamResults])

	// Refresh the file list when the task is done
	useEffect(() => {
		if (streamError?.status) {
			addAlert(streamError.message, 'error')
		}
	}, [streamDone, streamError])

	const saveOptionsToFile = async (): Promise<string | undefined> => {
		if (!directoryPath) return

		const optionsObject = entries[0].toObject()

		// Convert relative paths to absolute paths if necessary
		const outputFolder = optionsObject['output_file_folder'].startsWith('.')
			? await join(directoryPath, optionsObject['output_file_folder'])
			: optionsObject['output_file_folder']

		// Add the absolute output folder to the options object
		optionsObject['output_file_folder'] = outputFolder

		const outputName = optionsObject['output_file_name']

		// Validate options
		if (
			!optionsObject['output_file_folder'] ||
			!outputName ||
			!optionsObject['neuroglancer_json'] ||
			optionsObject['output_file_folder'] === '' ||
			outputName === '' ||
			optionsObject['neuroglancer_json'] === ''
		) {
			return
		}

		const modifiedName = `${outputName}-slice-options.json`

		// Save options to file
		await writeFile(outputFolder, modifiedName, JSON.stringify(optionsObject, null, 4))

		const outputOptions = await join(outputFolder, modifiedName)

		return outputOptions
	}

	const requestVisualization = async (): Promise<void> => {
		if (!directoryPath) return

		if (onDemandVisualizationResults) clearFetch('/create_slice_visualization/')

		// Save the options to a file
		const outputOptions = await saveOptionsToFile()

		if (!outputOptions) return

		// Run the visualization
		performFetch('/create_slice_visualization/', { options: outputOptions })
	}

	////// HANDLE ENTRY CHANGES IN OPTIONS PANEL /////////
	const onEntryChange = async (entry: Entry): Promise<void> => {
		if (entry.name === 'neuroglancer_json' && directoryPath) {
			if (entry.value === '') return

			const neuroglancerJSONContent = await readFile('', entry.value as string)

			if (!neuroglancerJSONContent || neuroglancerJSONContent === '') {
				addAlert('Invalid Neuroglancer JSON', 'error')
				return
			}

			let json = ''

			try {
				json = JSON.parse(neuroglancerJSONContent)
			} catch (e) {
				addAlert('Invalid Neuroglancer JSON', 'error')
				return
			}

			const jsonResult = safeParse(NeuroglancerJSONSchema, json)

			if (jsonResult.success) {
				const imageLayers: { type: string; name: string }[] = []
				const annotationLayers: { type: string; name: string }[] = []

				// Read all image and annotation layers from the Neuroglancer JSON
				for (const layer of jsonResult.output['layers']) {
					if (layer.type === 'image' && layer.name !== '') {
						imageLayers.push(layer)
					} else if (layer.type === 'annotation' && layer.name !== '') {
						annotationLayers.push(layer)
					}
				}

				// Update the options for the image and annotation layer entries
				if (entries[0] instanceof CompoundEntry) {
					entries[0].getEntries().forEach((entry) => {
						if (entry.name === 'neuroglancer_image_layer' && entry instanceof Entry) {
							entry.options = imageLayers.map((layer) => layer.name)

							if (imageLayers.length > 0) entry.value = imageLayers[0].name
						} else if (
							entry.name === 'neuroglancer_annotation_layer' &&
							entry instanceof Entry
						) {
							entry.options = annotationLayers.map((layer) => layer.name)

							if (annotationLayers.length > 0) entry.value = annotationLayers[0].name
						}
					})

					setEntries([...entries])
				}
			} else {
				addAlert('Invalid Neuroglancer JSON', 'error')
			}
		}

		// Request visualization when the Neuroglancer JSON, slice dimensions, or bounding box params are changed
		const visualizationEntries = [
			'neuroglancer_json',
			'neuroglancer_annotation_layer',
			'slice_width',
			'slice_height',
			'dist_between_slices',
			'bounding_box',
			'max_depth',
			'target_slices_per_box'
		]

		const streamInProgress = !streamDone && progress.length > 0

		if (visualizationEntries.includes(entry.name) && entry.value !== '' && !streamInProgress) {
			requestVisualization()
		}
	}

	//////// HANDLE OPTIONS FORM SUBMISSION /////////
	const onSubmit = async (): Promise<void> => {
		if (!connected || !directoryPath) {
			return
		}

		const results = safeParse(SliceResultSchema, sliceResults)

		// Delete the previous task if it exists
		if (results.success) {
			performFetch('/delete/', results.output, { method: 'POST' }).then(() => {
				// Clear the task once it has been deleted
				clearFetch('/slice/')
				clearStream(SLICE_STREAM)
			})
		}

		const outputOptions = await saveOptionsToFile()

		if (!outputOptions) return

		// Run the slice generation
		performFetch('/slice/', { options: outputOptions }, { method: 'POST' })
	}

	////// HANDLE FILE DROP ONTO HEADER OF OPTIONS PANEL //////
	const onHeaderDrop = async (content: string): Promise<void> => {
		if (!directoryPath || !content || content === '') return

		const fileContent = await readFile('', content)

		let jsonContent = null

		try {
			jsonContent = JSON.parse(fileContent)
		} catch (e) {
			addAlert('Invalid JSON file', 'error')
			return
		}

		const schema = entries[0].toSchema()

		const parseResult = safeParse(schema, jsonContent)

		if (!parseResult.success) {
			addAlert(
				'Wrong JSON file format. Make sure you provide a slice options JSON file.',
				'error'
			)
			return
		}

		// Update the entries with the new values from the file
		entries[0].setValue(parseResult.output as CompoundValueType)
		setEntries([...entries])

		// Update the neuroglancer JSON entry
		if (entries[0] instanceof CompoundEntry) {
			const neuroglancerJSONEntry = entries[0].findEntry('neuroglancer_json')

			if (neuroglancerJSONEntry instanceof Entry)
				onEntryChange(entries[0].findEntry('neuroglancer_json') as Entry)
		}
	}

	const boundingBoxProgress = visualizationData
		? (progress.find(([name]) => name === SLICE_STEP_NAME) ?? [SLICE_STEP_NAME, 0.0])[1]
		: 0.0

	return {
		progress,
		boundingBoxProgress,
		connected,
		entries,
		onSubmit,
		visualizationData,
		onEntryChange,
		onHeaderDrop,
		setDropNodeRef,
		isOver
	}
}

type VisualizationInput = {
	rects: number[][][]
	bounding_boxes: { min: number[]; max: number[] }[]
	link_rects: number[]
}

type VisualizationOutput = {
	rects: { topLeft: number[]; topRight: number[]; bottomRight: number[]; bottomLeft: number[] }[]
	boundingBoxes: { min: number[]; max: number[] }[]
	linkRects: number[]
}

function visualizationDataToProps(
	visualizationData: VisualizationInput | null
): VisualizationOutput | null {
	if (!visualizationData) {
		return null
	}

	const rects = visualizationData.rects.map((rect) => {
		return { topLeft: rect[0], topRight: rect[1], bottomRight: rect[2], bottomLeft: rect[3] }
	})
	const boundingBoxes = visualizationData.bounding_boxes
	const linkRects = visualizationData.link_rects

	return { rects, boundingBoxes, linkRects }
}

export default SlicesPage

function convertConfigJSONToProps(configJSON: ConfigurationJSON): VisualizationOutput {
	const rects = configJSON.slice_rects
	const boundingBoxes = configJSON.volume_cache.bounding_boxes.map((box) => {
		return { min: [box.x_min, box.y_min, box.z_min], max: [box.x_max, box.y_max, box.z_max] }
	})
	const linkRects = configJSON.volume_cache.link_rects

	return visualizationDataToProps({
		rects,
		bounding_boxes: boundingBoxes,
		link_rects: linkRects
	})!
}
