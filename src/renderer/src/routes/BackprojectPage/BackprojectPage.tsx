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

const BACKPROJECT_STREAM = '/backproject_status_stream/'

function BackprojectPage(): JSX.Element {
	const { connected, performFetch, performStream, useFetchListener, useStreamListener } =
		useContext(ServerContext)
	const { directoryPath, refreshDirectory } = useContext(DirectoryContext)

	const [entries] = useState<(Entry | CompoundEntry)[]>([new BackprojectOptionsFile()])

	const onSubmit = async () => {
		if (!connected) {
			return
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

		refreshDirectory()

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

	const { addAlert } = useContext(AlertContext)

	const [progress, setProgress] = useState<any>([])

	const { results: fetchResults } = useFetchListener('/backproject/')
	const {
		results: streamResults,
		error: streamError,
		done: streamDone
	} = useStreamListener(BACKPROJECT_STREAM)

	// Listen to the status stream for the active task
	useEffect(() => {
		if (fetchResults && 'task_id' in fetchResults) {
			performStream(BACKPROJECT_STREAM, fetchResults)
		}
	}, [fetchResults])

	// Update the progress state when new data is received
	useEffect(() => {
		if (streamResults && 'progress' in streamResults) {
			if (!('error' in streamResults && streamResults.error)) {
				setProgress(streamResults.progress)
			}
		}
	}, [streamResults])

	// Refresh the file list when the task is done
	useEffect(() => {
		refreshDirectory()

		if (streamError?.status) {
			addAlert(streamError.message, 'error')
		}

		// if (streamDone && !streamError?.status) {
		// 	addAlert('Task completed successfully!', 'success')
		// 	refreshDirectory()

		// 	// Delete the task from the server
		// 	if (fetchResults && 'task_id' in fetchResults) {
		// 		performFetch('/delete/', fetchResults, { method: 'POST' })
		// 	}
		// } else if (streamError?.status) {
		// 	addAlert(streamError.message, 'error')
		// 	refreshDirectory()

		// 	// Delete the task from the server
		// 	if (fetchResults && 'task_id' in fetchResults) {
		// 		performFetch('/delete/', fetchResults, { method: 'POST' })
		// 	}
		// }
	}, [streamDone, streamError])

	return (
		<div className={styles.backprojectPage}>
			<VisualizePanel></VisualizePanel>
			<ProgressPanel progress={progress} connected={connected} />
			<OptionsPanel entries={entries} onSubmit={onSubmit} />
		</div>
	)
}

export default BackprojectPage
