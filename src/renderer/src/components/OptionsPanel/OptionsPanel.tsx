import Header from '../Header/Header'
import OptionEntry from './components/OptionEntry/OptionEntry'
import OptionSubmit from './components/OptionSubmit/OptionSubmit'
import styles from './OptionsPanel.module.css'

function OptionsPanel(): JSX.Element {
	const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
		e.preventDefault()

		// const form = e.target as HTMLFormElement
		// const formData = new FormData(form)

		// for (let [key, value] of formData.entries()) {
		// 	console.log(`${key}: ${value}`)
		// }
	}

	return (
		<div className="panel">
			<form className={styles.form} method="post" onSubmit={handleSubmit}>
				<Header text={'Options'} />
				<OptionEntry label={'Slice Width'} initialValue={120} inputType={'number'} />
				<OptionEntry label={'Slice Height'} initialValue={120} inputType={'number'} />
				<OptionEntry
					label={'Output File Name'}
					initialValue={'sample'}
					inputType={'string'}
				/>
				<OptionEntry
					label={'Distance Between Slices'}
					initialValue={1}
					inputType={'number'}
				/>
				<OptionEntry
					label={'Flush CloudVolume Cache'}
					initialValue={false}
					inputType={'boolean'}
				/>
				<OptionSubmit />
			</form>
		</div>
	)
}

export default OptionsPanel
