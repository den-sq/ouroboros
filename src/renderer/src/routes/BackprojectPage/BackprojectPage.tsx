import OptionsPanel from '@renderer/components/OptionsPanel/OptionsPanel'
import styles from './BackprojectPage.module.css'
import VisualizePanel from '@renderer/components/VisualizePanel/VisualizePanel'
import ProgressPanel from '@renderer/components/ProgressPanel/Progress'
import { ServerContext } from '@renderer/contexts/ServerContext'
import { CompoundEntry, Entry, BackprojectOptionsFile } from '@renderer/lib/options'
import { useContext, useEffect, useState } from 'react'
import { DirectoryContext } from '@renderer/contexts/DirectoryContext'
import { join, writeFile } from '@renderer/lib/file'
import { AlertContext } from '@renderer/contexts/AlertContext'
import { safeParse } from 'valibot'
import BackprojectResultSchema from '@renderer/schemas/backproject-result-schema'
import BackprojectStatusResultSchema from '@renderer/schemas/backproject-status-result-schema'

const BACKPROJECT_STREAM = '/backproject_status_stream/'

function BackprojectPage(): JSX.Element {
	const { progress, connected, entries, onSubmit } = useBackprojectPageState()

	return (
		<div className={styles.backprojectPage}>
			<VisualizePanel></VisualizePanel>
			<ProgressPanel progress={progress} connected={connected} />
			<OptionsPanel entries={entries} onSubmit={onSubmit} />
		</div>
	)
}

function useBackprojectPageState() {
	const {
		connected,
		performFetch,
		performStream,
		useFetchListener,
		useStreamListener,
		clearFetch,
		clearStream
	} = useContext(ServerContext)
	const { directoryPath } = useContext(DirectoryContext)

	const [entries] = useState<(Entry | CompoundEntry)[]>([new BackprojectOptionsFile()])

	const { addAlert } = useContext(AlertContext)

	const [progress, setProgress] = useState<any>([])

	const { results: backprojectResults } = useFetchListener('/backproject/')
	const {
		results: streamResults,
		error: streamError,
		done: streamDone
	} = useStreamListener(BACKPROJECT_STREAM)

	// Listen to the status stream for the active task
	useEffect(() => {
		const results = safeParse(BackprojectResultSchema, backprojectResults)

		if (results.success) {
			performStream(BACKPROJECT_STREAM, results.output)
		}
	}, [backprojectResults])

	// Update the progress state when new data is received
	useEffect(() => {
		const results = safeParse(BackprojectStatusResultSchema, streamResults)

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

	const onSubmit = async () => {
		if (!connected || !directoryPath) {
			return
		}

		const results = safeParse(BackprojectResultSchema, backprojectResults)

		// Delete the previous task if it exists
		if (results.success) {
			performFetch('/delete/', results.output, { method: 'POST' }).then(() => {
				// Clear the task once it has been deleted
				clearFetch('/slice/')
				clearStream(BACKPROJECT_STREAM)
			})
		}

		const optionsObject = entries[0].toObject()

		const outputFolder = await join(directoryPath, optionsObject['output_file_folder'])

		// Add the absolute output folder to the options object
		optionsObject['output_file_folder'] = outputFolder

		const outputName = optionsObject['output_file_name']
		const straightenedVolumePath = await join(
			directoryPath,
			optionsObject['straightened_volume_path']
		)
		optionsObject['straightened_volume_path'] = straightenedVolumePath
		const configPath = await join(directoryPath, optionsObject['config_path'])
		optionsObject['config_path'] = configPath

		// Validate options
		if (
			!optionsObject['output_file_folder'] ||
			!outputName ||
			!optionsObject['straightened_volume_path'] ||
			!optionsObject['config_path'] ||
			optionsObject['output_file_folder'] === '' ||
			outputName === '' ||
			optionsObject['straightened_volume_path'] === '' ||
			optionsObject['config_path'] === ''
		) {
			return
		}

		const modifiedName = `${outputName}-backproject-options.json`

		// Save options to file
		await writeFile(outputFolder, modifiedName, JSON.stringify(optionsObject, null, 4))

		const outputOptions = await join(outputFolder, modifiedName)

		// Run the slice generation
		performFetch(
			'/backproject/',
			{
				options: outputOptions
			},
			{ method: 'POST' }
		)
	}

	return { progress, connected, entries, onSubmit }
}

export default BackprojectPage
