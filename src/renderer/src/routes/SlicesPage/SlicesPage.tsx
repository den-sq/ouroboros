import OptionsPanel from '@renderer/components/OptionsPanel/OptionsPanel'
import styles from './SlicesPage.module.css'
import VisualizePanel from '@renderer/components/VisualizePanel/VisualizePanel'
import ProgressPanel from '@renderer/components/ProgressPanel/Progress'
import { ServerContext } from '@renderer/contexts/ServerContext'
import { CompoundEntry, Entry, SliceOptionsFile } from '@renderer/lib/options'
import { useContext, useEffect, useState } from 'react'
import { DirectoryContext } from '@renderer/contexts/DirectoryContext'
import { join, readFile, writeFile } from '@renderer/lib/file'
import { AlertContext } from '@renderer/contexts/AlertContext'
import VisualizeSlicing from './components/VisualizeSlicing/VisualizeSlicing'
import SliceResultSchema from '@renderer/schemas/slice-result-schema'
import { safeParse } from 'valibot'
import SliceStatusResultSchema from '@renderer/schemas/slice-status-result-schema'
import NeuroglancerJSONSchema from '@renderer/schemas/neuroglancer-json-schema'

const SLICE_RENDER_PROPORTION = 0.01

const SLICE_STREAM = '/slice_status_stream/'

function SlicesPage(): JSX.Element {
	const { progress, connected, entries, onSubmit, visualizationResults, onEntryChange } =
		useSlicePageState()

	const visualizationData =
		visualizationResults && 'data' in visualizationResults
			? visualizationDataToProps(
					visualizationResults.data as {
						rects: number[][][]
						bounding_boxes: { min: number[]; max: number[] }[]
						link_rects: number[]
					}
				)
			: null

	return (
		<div className={styles.slicePage}>
			<VisualizePanel>
				{visualizationData ? (
					<VisualizeSlicing
						{...visualizationData}
						useEveryNthRect={Math.floor(
							visualizationData.rects.length * SLICE_RENDER_PROPORTION
						)}
					/>
				) : null}
			</VisualizePanel>
			<ProgressPanel progress={progress} connected={connected} />
			<OptionsPanel entries={entries} onSubmit={onSubmit} onEntryChange={onEntryChange} />
		</div>
	)
}

function visualizationDataToProps(
	visualizationData: {
		rects: number[][][]
		bounding_boxes: { min: number[]; max: number[] }[]
		link_rects: number[]
	} | null
) {
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

function useSlicePageState() {
	const {
		connected,
		performFetch,
		useFetchListener,
		performStream,
		useStreamListener,
		clearFetch,
		clearStream
	} = useContext(ServerContext)
	const { directoryPath, refreshDirectory } = useContext(DirectoryContext)

	const [entries] = useState<(Entry | CompoundEntry)[]>([new SliceOptionsFile()])

	const { addAlert } = useContext(AlertContext)

	const [progress, setProgress] = useState<any>([])

	const { results: sliceResults } = useFetchListener('/slice/')
	const {
		results: streamResults,
		error: streamError,
		done: streamDone
	} = useStreamListener(SLICE_STREAM)

	const { results: visualizationResults } = useFetchListener('/slice_visualization/')

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
		refreshDirectory()

		if (streamError?.status) {
			addAlert(streamError.message, 'error')
		}

		const results = safeParse(SliceResultSchema, sliceResults)

		if (streamDone && results.success) {
			// Get the visualization data
			performFetch('/slice_visualization/', results.output)
		}
	}, [streamDone, streamError])

	const onEntryChange = async (entry: Entry) => {
		if (entry.name === 'neuroglancer_json') {
			if (entry.value === '') return

			const neuroglancerJSONContent = await readFile(directoryPath, entry.value as string)

			if (!neuroglancerJSONContent || neuroglancerJSONContent === '') {
				addAlert('Invalid Neuroglancer JSON', 'error')
			}

			let json = ''

			try {
				json = JSON.parse(neuroglancerJSONContent)
			} catch (e) {
				addAlert('Invalid Neuroglancer JSON', 'error')
			}

			const jsonResult = safeParse(NeuroglancerJSONSchema, json)

			if (jsonResult.success) {
				const imageLayers: { type: string; name: string }[] = []
				const annotationLayers: { type: string; name: string }[] = []

				for (const layer of jsonResult.output['layers']) {
					if (layer.type === 'image' && layer.name !== '') {
						imageLayers.push(layer)
					} else if (layer.type === 'annotation' && layer.name !== '') {
						annotationLayers.push(layer)
					}
				}

				console.log(imageLayers, annotationLayers)
			}
		}
	}

	const onSubmit = async () => {
		if (!connected) {
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

		const optionsObject = entries[0].toObject()

		const outputFolder = await join(directoryPath, optionsObject['output_file_folder'])

		// Add the absolute output folder to the options object
		optionsObject['output_file_folder'] = outputFolder

		const outputName = optionsObject['output_file_name']
		const neuroglancerJSON = await join(directoryPath, optionsObject['neuroglancer_json'])
		optionsObject['neuroglancer_json'] = neuroglancerJSON

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

		refreshDirectory()

		const outputOptions = await join(outputFolder, modifiedName)

		// Run the slice generation
		performFetch('/slice/', { options: outputOptions }, { method: 'POST' })
	}

	return { progress, connected, entries, onSubmit, visualizationResults, onEntryChange }
}

export default SlicesPage
