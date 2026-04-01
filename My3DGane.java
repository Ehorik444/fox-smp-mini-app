package com.example.my3dgame;

import com.badlogic.gdx.ApplicationAdapter;
import com.badlogic.gdx.Gdx;
import com.badlogic.gdx.Input;
import com.badlogic.gdx.graphics.Color;
import com.badlogic.gdx.graphics.PerspectiveCamera;
import com.badlogic.gdx.graphics.VertexAttributes;
import com.badlogic.gdx.graphics.g3d.*;
import com.badlogic.gdx.graphics.g3d.attributes.ColorAttribute;
import com.badlogic.gdx.graphics.g3d.utils.ModelBuilder;
import com.badlogic.gdx.math.Vector3;

public class My3DGame extends ApplicationAdapter {
    PerspectiveCamera cam;
    ModelBatch modelBatch;
    Model playerModel;
    Model platformModel;
    ModelInstance playerInstance;
    ModelInstance platformInstance;
    Environment environment;

    @Override
    public void create () {
        // Инициализация камеры
        cam = new PerspectiveCamera(67, Gdx.graphics.getWidth(), Gdx.graphics.getHeight());
        cam.position.set(0f, 5f, 5f);
        cam.lookAt(0, 0, 0);
        cam.near = 0.1f;
        cam.far = 300f;
        cam.update();

        // Инициализация батча для рендеринга 3D моделей
        modelBatch();

        // Создание модели игрока (куб)
        ModelBuilder modelBuilder = new ModelBuilder();
        playerModel = modelBuilder.createBox(1f, 1f, 1f,
                new Material(ColorAttribute.createDiffuse(Color.BLUE)),
                VertexAttributes.Usage.Position | VertexAttributes.Usage.Normal);

        // Создание модели платформы (плоскость)
        platformModel = modelBuilder.createRect(
                -5f, 0f, -5f,  // нижний левый
                5f, 0f, -5f,   // нижний правый
                5f, 0f, 5f,    // верхний правый
                -5f, 0f, 5f,   // верхний левый
                0f, 1f, 0f,    // нормаль вверх
                new Material(ColorAttribute.createDiffuse(Color.GREEN)),
                VertexAttributes.Usage.Position | VertexAttributes.Usage.Normal);

        // Создание инстансов
        playerInstance = new ModelInstance(playerModel, 0f, 1f, 0f); // Начальная позиция игрока
        platformInstance = new ModelInstance(platformModel, 0f, 0f, 0f);

        // Окружение (для освещения)
        environment = new Environment();
        environment.set(new ColorAttribute(ColorAttribute.AmbientLight, 0.8f, 0.8f, 0.8f, 1f));
    }

    @Override
    public void render () {
        // Обновление камеры
        cam.update();

        // Управление игроком
        Vector3 movement = new Vector3(0, 0, 0);
        float moveSpeed = 3f * Gdx.graphics.getDeltaTime(); // Скорость движения зависит от FPS

        if (Gdx.input.isKeyPressed(Input.Keys.W)) movement.add(0, 0, -moveSpeed); // Вперед
        if (Gdx.input.isKeyPressed(Input.Keys.S)) movement.add(0, 0, moveSpeed);  // Назад
        if (Gdx.input.isKeyPressed(Input.Keys.A)) movement.add(-moveSpeed, 0, 0); // Влево
        if (Gdx.input.isKeyPressed(Input.Keys.D)) movement.add(moveSpeed, 0, 0);  // Вправо

        playerInstance.transform.translate(movement);

        // Центрируем камеру над игроком (третий вид)
        cam.position.set(playerInstance.transform.getTranslation(new Vector3()).add(0, 5, 5));
        cam.lookAt(playerInstance.transform.getTranslation(new Vector3()).mulAdd(Vector3.Y, 1f));
        cam.update();

        // Рендеринг
        modelBatch.begin(cam);
        modelBatch.render(platformInstance, environment);
        modelBatch.render(playerInstance, environment);
        modelBatch.end();
    }

    @Override
    public void dispose () {
        modelBatch.dispose();
        playerModel.dispose();
        platformModel.dispose();
    }
}