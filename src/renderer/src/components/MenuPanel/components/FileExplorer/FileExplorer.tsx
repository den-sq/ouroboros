import Header from '@renderer/components/Header/Header'
import styles from './FileExplorer.module.css'
import FileEntry from './components/FileEntry/FileEntry'

function FileExplorer(): JSX.Element {
	// TODO: Header should be the folder name
	return (
		<div className={styles.fileExplorerPanel}>
			<Header text="Files" />
			<FileEntry name={'sample-backprojected'} path="./sample-backprojected" type="folder" />
			<FileEntry
				name={'sample-backprojected.tif'}
				path="./sample-backprojected.tif"
				type="image"
			/>
			<FileEntry
				name={'sample-configuration.json'}
				path="./sample-configuration.json"
				type="file"
			/>
			<FileEntry name={'sample-slices'} path="./sample-slices" type="folder" />
			<FileEntry name={'sample.tif'} path="./sample.tif" type="image" />
		</div>
	)
}

export default FileExplorer
