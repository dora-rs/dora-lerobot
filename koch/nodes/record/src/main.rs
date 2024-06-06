use dora_node_api::{
    DoraNode,
    Event
};

use std::{
    error::Error,
    env,
    time::Duration
};

use rustypot::{
    DynamixelSerialIO,
    device::{
        xl330
    }
};

fn main() -> Result<(), Box<dyn Error>> {
    // Retrieve 'arm_port' as str and 'arm_servo_count' as int from environment
    let arm_port = env::var("ARM_PORT").expect("ARM_PORT must be set");
    println!("ARM_PORT: {}", arm_port);

    let mut serial_port = serialport::new(arm_port, 1_000_000).timeout(Duration::from_millis(2)).open().expect("Failed to open port");

    // Enable torque for gripper
    let io = DynamixelSerialIO::v2();
    xl330::sync_write_torque_enable(
        &io,
        serial_port.as_mut(),
        &[4],
        &[1; 1],
    ).expect("Communication error");

    let (mut node, mut events) = DoraNode::init_from_env()?;

    while let Some(event) = events.recv() {
        match event {
            Event::Input {
                id,
                metadata,
                data: _,
            } => match id.as_str() {
                "tick" => {
                    let pos = xl330::sync_read_present_position(
                        &io,
                        serial_port.as_mut(),
                        &[0, 1, 2, 3, 4],
                    ).expect("Read Communication error");

                    println!("{:?}", pos);
                }
                other => eprintln!("Received input `{other}`"),
            },
            _ => {}
        }
    }

    Ok(())
}
