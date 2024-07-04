import Header from '@renderer/components/Header/Header'
import styles from './FileExplorer.module.css'
import FileEntry from './components/FileEntry/FileEntry'

function FileExplorer(): JSX.Element {
	const fileEntries = [
		<FileEntry
			name={'sample-backprojected'}
			path="./sample-backprojected"
			key="./sample-backprojected"
			type="folder"
		/>,
		<FileEntry
			name={'sample-backprojected.tif'}
			path="./sample-backprojected.tif"
			key="./sample-backprojected.tif"
			type="image"
		/>,
		<FileEntry
			name={'sample-configuration.json'}
			path="./sample-configuration.json"
			key="./sample-configuration.json"
			type="file"
		/>,
		<FileEntry
			name={'sample-slices'}
			path="./sample-slices"
			key="./sample-slices"
			type="folder"
		/>,
		<FileEntry name={'sample.tif'} path="./sample.tif" key="./sample.tif" type="image" />
	]

	// TODO: Header should be the folder name
	return (
		<div className={styles.fileExplorerPanel}>
			<Header text="Files" />
			<div>{fileEntries}</div>
		</div>
	)
}

export default FileExplorer
