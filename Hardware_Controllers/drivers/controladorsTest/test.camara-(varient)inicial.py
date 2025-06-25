# --- Exemple d'ús per Camera ---
if __name__ == "__main__":
    import time

    print("--- Test de la Classe Camera ---")

    # Simulem una estructura de projecte per al test
    PROJECT_ROOT_NAME = "ProjecteMultimediaTest_Camera"
    SCRIPTS_FOLDER = "programes"
    DATA_FOLDER = "dades_media"
    CAM_CAPTURE_DIR = "captures_cam"

    project_root_for_test = os.path.abspath(PROJECT_ROOT_NAME)
    scripts_dir_for_test = os.path.join(project_root_for_test, SCRIPTS_FOLDER)
    data_dir_for_test = os.path.join(project_root_for_test, DATA_FOLDER)
    
    if os.path.exists(project_root_for_test):
        shutil.rmtree(project_root_for_test)
        print(f"Directori de prova '{project_root_for_test}' netejat.")
    
    os.makedirs(scripts_dir_for_test, exist_ok=True)
    # Creem un fitxer fals per simular la ruta dels scripts
    with open(os.path.join(scripts_dir_for_test, "camera.py"), "w") as f: f.write("# camera")
    with open(os.path.join(scripts_dir_for_test, "file_manager.py"), "w") as f: f.write("# file_manager")


    # Canviem el directori de treball per simular l'execució des d'un altre lloc
    execution_dir_for_test = os.path.abspath("execucions_test_camera")
    if os.path.exists(execution_dir_for_test):
        shutil.rmtree(execution_dir_for_test)
    os.makedirs(execution_dir_for_test, exist_ok=True)
    
    original_cwd = os.getcwd()
    os.chdir(execution_dir_for_test)
    print(f"\n--- Canviat el directori de treball a: {os.getcwd()} ---")

    try:
        with Camera(
            nom_camera="Càmera de Prova",
            capture_dir=CAM_CAPTURE_DIR,
            default_prefix="robot_cam",
            scripts_folder_name=SCRIPTS_FOLDER,
            data_folder_name=DATA_FOLDER
        ) as cam:
            print("\nCapturant una imatge amb FileManager...")
            filepath1 = cam.save_image(extension="png")
            if filepath1:
                print(f"Imatge guardada a: {filepath1}")
            else:
                print("No s'ha pogut guardar la primera imatge.")
            time.sleep(1)

            print("\nCapturant una segona imatge...")
            filepath2 = cam.save_image(extension="jpg")
            if filepath2:
                print(f"Imatge guardada a: {filepath2}")
            else:
                print("No s'ha pogut guardar la segona imatge.")
            time.sleep(1)

            print("\nHistorial de captures:")
            history = cam.get_file_manager().get_capture_history()
            for i, fpath in enumerate(history):
                print(f"  {i}: {os.path.basename(fpath)}")
            
            if filepath1:
                print(f"\nEliminant la primera imatge de prova '{os.path.basename(filepath1)}'...")
                cam.get_file_manager().delete_capture_file(filepath1)
            
            print("\nHistorial després d'eliminar:")
            history_after_delete = cam.get_file_manager().get_capture_history()
            for i, fpath in enumerate(history_after_delete):
                print(f"  {i}: {os.path.basename(fpath)}")

    except Exception as e:
        print(f"\nS'ha produït un error durant el test de la càmera: {e}")
    finally:
        os.chdir(original_cwd)
        print(f"\n--- Test de la Càmera Finalitzat. Tornat al directori original: {os.getcwd()} ---")
        # Pots descomentar això si vols netejar els directoris de prova automàticament:
        # if os.path.exists(project_root_for_test):
        #     shutil.rmtree(project_root_for_test)
        # if os.path.exists(execution_dir_for_test):
        #     shutil.rmtree(execution_dir_for_test)
